from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router)
