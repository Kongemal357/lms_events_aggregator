from fastapi import APIRouter

from src.api.routes import health, events, sync

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(events.router)
api_router.include_router(sync.router)