from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.clients.events_provider import EventsProviderClient
from src.core.database import get_session
from src.core.repositories.events import EventRepository
from src.core.repositories.sync import SyncRepository
from src.core.usecases.get_event_detail import GetEventDetailUsecase
from src.core.usecases.get_events import GetEventsUsecase
from src.core.usecases.get_seats import GetSeatsUsecase
from src.core.usecases.sync_events import SyncEventsUsecase

# ─── Repositories ─────────────────────────


async def get_events_repo(session: AsyncSession = Depends(get_session)) -> EventRepository:
    """Return EventRepository bound to the current database session."""
    return EventRepository(session)


async def get_sync_repo(session: AsyncSession = Depends(get_session)) -> SyncRepository:
    """Return SyncRepository bound to the current database session."""
    return SyncRepository(session)


# ─── External clients ─────────────────────


async def get_client() -> EventsProviderClient:
    """Return a configured EventsProviderClient.

    Reads EVENTS_PROVIDER_URL and EVENTS_PROVIDER_API_KEY from environment.
    """
    return EventsProviderClient()


# ─── UseCases ─────────────────────────────


async def get_events_usecase(
    repo: EventRepository = Depends(get_events_repo),
) -> GetEventsUsecase:
    """Return GetEventsUsecase for listing events."""
    return GetEventsUsecase(repo)


async def get_event_detail_usecase(
    repo: EventRepository = Depends(get_events_repo),
) -> GetEventDetailUsecase:
    """Return GetEventDetailUsecase for fetching a single event."""
    return GetEventDetailUsecase(repo)


async def get_sync_usecase(
    client: EventsProviderClient = Depends(get_client),
    events_repo: EventRepository = Depends(get_events_repo),
    sync_repo: SyncRepository = Depends(get_sync_repo),
) -> SyncEventsUsecase:
    """Return SyncEventsUsecase with all required dependencies."""
    return SyncEventsUsecase(client, events_repo, sync_repo)


async def get_seats_usecase(
    client: EventsProviderClient = Depends(get_client),
    events_repo: EventRepository = Depends(get_events_repo),
) -> GetSeatsUsecase:
    """Return GetSeatsUsecase for fetching available seats from provider.

    Results are cached in memory for 30 seconds.
    """
    return GetSeatsUsecase(client, events_repo)
