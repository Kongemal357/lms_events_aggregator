import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Event


class EventRepository:
    """Data access layer for Event model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, event_id: uuid.UUID) -> Event | None:
        """Return active event by ID or None."""
        result = await self.session.execute(
            select(Event).where(Event.id == event_id, Event.is_active)
        )
        return result.scalar_one_or_none()

    async def get_all_active(
        self,
        date_from: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Event], int]:
        """Return paginated active events, optionally filtered by date_from."""
        base = select(Event).where(Event.is_active)
        count_base = select(func.count(Event.id)).where(Event.is_active)

        if date_from:
            base = base.where(Event.event_time >= date_from)
            count_base = count_base.where(Event.event_time >= date_from)

        total = (await self.session.execute(count_base)).scalar() or 0

        offset = (page - 1) * page_size
        query = base.order_by(Event.event_time).offset(offset).limit(page_size)
        events = (await self.session.execute(query)).scalars().all()

        return events, total

    async def upsert(self, event_data: dict) -> Event:
        """Create or update an event from provider data."""
        for field in ("event_time", "registration_deadline", "changed_at", "provider_created_at"):
            if field in event_data and isinstance(event_data[field], str):
                event_data[field] = datetime.fromisoformat(event_data[field])

        existing = await self.get_by_id(event_data["id"])

        if existing:
            for field in (
                "name",
                "event_time",
                "registration_deadline",
                "status",
                "number_of_visitors",
                "place_id",
                "place_name",
                "place_city",
                "place_address",
                "place_seats_pattern",
                "changed_at",
                "provider_created_at",
            ):
                if field in event_data:
                    setattr(existing, field, event_data[field])
            existing.is_active = True
            existing.last_synced_at = datetime.now(timezone.utc)
            await self.session.commit()
            return existing
        else:
            event = Event(
                **{k: v for k, v in event_data.items() if hasattr(Event, k)},
                is_active=True,
                last_synced_at=datetime.now(timezone.utc),
            )
            self.session.add(event)
            await self.session.commit()
            return event

    async def deactivate_missing(self, active_ids: set[uuid.UUID]) -> int:
        """Mark events as inactive if they are not in active_ids. Returns count."""
        result = await self.session.execute(
            update(Event)
            .where(Event.id.not_in(active_ids), Event.is_active)
            .values(is_active=False, last_synced_at=datetime.now(timezone.utc))
        )
        await self.session.commit()
        return result.rowcount
