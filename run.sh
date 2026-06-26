#!/bin/bash
set -e

export DATABASE_URL="postgresql+asyncpg://${POSTGRES_USERNAME}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DATABASE_NAME}"

source .venv/bin/activate
alembic upgrade head
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
