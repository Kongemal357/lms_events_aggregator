#!/bin/bash
set -e

export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USERNAME}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE_NAME}"

uv run python -c "import asyncio; from src.core.database import init_db; asyncio.run(init_db())"
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8000