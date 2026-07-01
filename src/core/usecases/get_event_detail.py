import uuid

from src.core.exeptions import EventNotFound
from src.core.repositories.events import EventRepository


class GetEventDetailUsecase:
    """Return a single event by ID from local database.

    Used by GET /api/events/{event_id}/.
    """

    def __init__(self, events_repo: EventRepository):
        self.events_repo = events_repo

    async def do(self, event_id: str) -> dict:
        """Fetch event by ID. Raises EventNotFound if missing or invalid UUID."""
        try:
            uid = uuid.UUID(event_id)
        except ValueError:
            raise EventNotFound()

        event = await self.events_repo.get_by_id(uid)
        if event is None:
            raise EventNotFound()

        return event
