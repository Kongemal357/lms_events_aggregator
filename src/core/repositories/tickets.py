from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import Ticket


class TicketRepository:
    """Data access layer for Ticket model."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        ticket_id: str,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:
        """Create a new active ticket."""
        ticket = Ticket(
            ticket_id=ticket_id,
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
            status="active",
        )
        self.session.add(ticket)
        await self.session.commit()
        return ticket

    async def get_active(self, ticket_id: str) -> Ticket | None:
        """Return active ticket by ticket_id (provider's ID)."""
        result = await self.session.execute(
            select(Ticket).where(
                Ticket.ticket_id == ticket_id,
                Ticket.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def cancel(self, ticket_id: str) -> None:
        """Mark ticket as cancelled."""
        await self.session.execute(
            update(Ticket)
            .where(Ticket.ticket_id == ticket_id, Ticket.status == "active")
            .values(status="cancelled")
        )
        await self.session.commit()
