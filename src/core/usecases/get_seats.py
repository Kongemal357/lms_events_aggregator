import uuid

from cachetools import TTLCache

from src.core.clients.events_provider import EventsProviderClient
from src.core.exeptions import EventNotFound, EventNotPublished
from src.core.logging import logger
from src.core.repositories.events import EventRepository
from src.core.schemas import SeatsResponse

_seats_cache: TTLCache = TTLCache(maxsize=1000, ttl=30)


class GetSeatsUsecase:
    """Return available seats for an event, cached for 30 seconds."""

    def __init__(self, client: EventsProviderClient, events_repo: EventRepository):
        self.client = client
        self.events_repo = events_repo

    async def do(self, event_id: uuid.UUID) -> SeatsResponse:
        event = await self.events_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFound()
        if event.status != "published":
            raise EventNotPublished()

        cache_key = str(event_id)
        if cache_key in _seats_cache:
            seats = _seats_cache[cache_key]
        else:
            seats = await self.client.get_seats(str(event_id))
            _seats_cache[cache_key] = seats

        return SeatsResponse(
            event_id=event_id,
            available_seats=seats,
        )
