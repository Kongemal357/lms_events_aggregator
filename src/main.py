import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.database import close_engine, AsyncSessionLocal
from src.core.logging import setup_logging, LoggingMiddleware, logger
from src.api.router import api_router
from src.api.error_handlers import add_exception_handlers
from src.core.clients.events_provider import EventsProviderClient
from src.core.repositories.events import EventRepository
from src.core.repositories.sync import SyncRepository
from src.core.usecases.sync_events import SyncEventsUsecase


async def run_periodic_sync():
    """Run sync every 24 hours."""
    while True:
        try:
            logger.info("scheduled_sync_started")
            async with AsyncSessionLocal() as session:
                client = EventsProviderClient()
                events_repo = EventRepository(session)
                sync_repo = SyncRepository(session)
                usecase = SyncEventsUsecase(client, events_repo, sync_repo)
                synced = await usecase.do()
                logger.info("scheduled_sync_completed", synced_count=synced)
        except Exception:
            logger.exception("scheduled_sync_failed")
        await asyncio.sleep(86400)  # 24 часа


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("application_startup")

    sync_task = asyncio.create_task(run_periodic_sync())

    yield

    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass

    await close_engine()
    logger.info("application_shutdown")


app = FastAPI(
    title="Events Aggregator",
    lifespan=lifespan,
    redirect_slashes=False,
)


add_exception_handlers(app)
app.add_middleware(LoggingMiddleware)
app.include_router(api_router)
