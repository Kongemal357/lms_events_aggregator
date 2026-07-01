from datetime import datetime, timezone

from src.core.clients.events_provider import EventsPaginator, EventsProviderClient
from src.core.exeptions import SyncInProgress
from src.core.repositories.events import EventRepository
from src.core.repositories.sync import SyncRepository


class SyncEventsUsecase:
    """Fetch events from provider and upsert into local DB."""

    def __init__(
        self,
        client: EventsProviderClient,
        events_repo: EventRepository,
        sync_repo: SyncRepository,
    ):
        self.client = client
        self.events_repo = events_repo
        self.sync_repo = sync_repo

    async def do(self) -> int:
        meta = await self.sync_repo.get()

        if meta.sync_status == "running":
            if meta.last_sync_started_at:
                elapsed = (datetime.now(timezone.utc) - meta.last_sync_started_at).total_seconds()
                if elapsed < 60:
                    raise SyncInProgress("Sync is already running")

        await self.sync_repo.update(meta.last_changed_at, "running")

        try:
            provider_ids: set[str] = set()
            synced_count = 0
            max_changed_at = meta.last_changed_at

            async for event_data in EventsPaginator(self.client, meta.last_changed_at):
                place = event_data.pop("place", {})
                event_data["place_id"] = place.get("id")
                event_data["place_name"] = place.get("name")
                event_data["place_city"] = place.get("city")
                event_data["place_address"] = place.get("address")
                event_data["place_seats_pattern"] = place.get("seats_pattern")

                if "created_at" in event_data:
                    event_data["provider_created_at"] = event_data.pop("created_at")

                provider_ids.add(event_data["id"])
                await self.events_repo.upsert(event_data)
                synced_count += 1

                changed_at = event_data.get("changed_at")
                if changed_at:
                    changed_str = (
                        changed_at if isinstance(changed_at, str) else changed_at.isoformat()
                    )
                    if changed_str > max_changed_at:
                        max_changed_at = changed_str

            if provider_ids:
                await self.events_repo.deactivate_missing(provider_ids)

            await self.sync_repo.update(max_changed_at, "idle")
            return synced_count

        except Exception:
            await self.sync_repo.update(meta.last_changed_at, "failed")
            raise
