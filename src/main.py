from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
