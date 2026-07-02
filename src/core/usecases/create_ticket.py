import uuid
from datetime import datetime, timezone

import httpx

from src.core.clients.events_provider import EventsProviderClient
from src.core.exeptions import (
    EventNotFound,
    EventNotPublished,
    RegistrationDeadlinePassed,
    SeatUnavailable,
)
from src.core.repositories.events import EventRepository
from src.core.repositories.tickets import TicketRepository
from src.core.schemas import TicketResponse


class CreateTicketUsecase:
    """Register a participant on an event."""

    def __init__(
        self,
        client: EventsProviderClient,
        events_repo: EventRepository,
        tickets_repo: TicketRepository,
    ):
        self.client = client
        self.events_repo = events_repo
        self.tickets_repo = tickets_repo

    async def do(
        self,
        event_id: uuid.UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> TicketResponse:
        event = await self.events_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFound()
        if event.status != "published":
            raise EventNotPublished()
        if event.registration_deadline < datetime.now(timezone.utc):
            raise RegistrationDeadlinePassed()

        try:
            ticket_id = await self.client.register(
                str(event_id), first_name, last_name, email, seat
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                try:
                    detail = e.response.json()
                except Exception:
                    detail = str(e)
                if isinstance(detail, list) and len(detail) > 0:
                    detail = detail[0]
                raise SeatUnavailable(str(detail))
            raise

        await self.tickets_repo.create(
            ticket_id=ticket_id,
            event_id=str(event_id),
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        return TicketResponse(ticket_id=ticket_id)
