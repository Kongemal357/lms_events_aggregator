from src.core.repositories.events import EventRepository
from src.core.schemas import EventListResponse


class GetEventsUsecase:
    """Return paginated list of events from local database.

    Used by GET /api/events/.
    """

    def __init__(self, events_repo: EventRepository):
        self.events_repo = events_repo

    async def do(
        self,
        date_from=None,
        page: int = 1,
        page_size: int = 20,
        base_url: str = "",
    ) -> EventListResponse:
        """Fetch active events with pagination and optional date filter.

        Args:
            date_from: Optional datetime filter — only events after this date.
            page: Page number (1-based).
            page_size: Number of events per page.
            base_url: Base URL of this service for building next/previous links.
        """
        events, total = await self.events_repo.get_all_active(date_from, page, page_size)
        return EventListResponse(
            count=total,
            next=self._build_next_url(base_url, page, page_size, total),
            previous=self._build_prev_url(base_url, page),
            results=events,
        )

    def _build_next_url(self, base_url: str, page: int, page_size: int, total: int) -> str | None:
        if page * page_size >= total:
            return None
        return f"{base_url}/api/events/?page={page + 1}&page_size={page_size}"

    def _build_prev_url(self, base_url: str, page: int) -> str | None:
        if page <= 1:
            return None
        return f"{base_url}/api/events/?page={page - 1}"