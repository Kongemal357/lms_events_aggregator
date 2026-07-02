# src/core/usecases/cancel_ticket.py
from datetime import datetime, timezone

from src.core.clients.events_provider import EventsProviderClient
from src.core.exeptions import EventAlreadyPassed, EventNotFound, TicketNotFound
from src.core.repositories.events import EventRepository
from src.core.repositories.tickets import TicketRepository
from src.core.schemas import CancelResponse


class CancelTicketUsecase:
    """Cancel a registration."""

    def __init__(
        self,
        client: EventsProviderClient,
        events_repo: EventRepository,
        tickets_repo: TicketRepository,
    ):
        self.client = client
        self.events_repo = events_repo
        self.tickets_repo = tickets_repo

    async def do(self, ticket_id: str) -> CancelResponse:
        ticket = await self.tickets_repo.get_active(ticket_id)
        if ticket is None:
            raise TicketNotFound()

        event = await self.events_repo.get_by_id(ticket.event_id)
        if event is None:
            raise EventNotFound()
        if event.event_time < datetime.now(timezone.utc):
            raise EventAlreadyPassed()

        await self.client.unregister(str(event.id), ticket_id)
        await self.tickets_repo.cancel(ticket_id)

        return CancelResponse(success=True)
