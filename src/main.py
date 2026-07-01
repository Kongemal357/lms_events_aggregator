from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.error_handlers import add_exception_handlers
from src.api.router import api_router
from src.core.database import close_engine
from src.core.logging import LoggingMiddleware, setup_logging, logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("application_startup")

    yield

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
