import logging
import os
from pathlib import Path
from typing import List
from uuid import uuid4

import structlog
import structlog.contextvars
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

LOG_DISABLED = os.getenv("LOG_DISABLED", "false").lower() == "true"
LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))

_logging_initialized = False


def setup_logging():
    global _logging_initialized
    if _logging_initialized:
        return
    _logging_initialized = True

    handlers: List[logging.Handler] = [logging.StreamHandler()]

    if not LOG_DISABLED:
        LOG_DIR.mkdir(exist_ok=True, parents=True)
        main_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
        error_handler = logging.FileHandler(LOG_DIR / "errors.log", encoding="utf-8")
        error_handler.setLevel(logging.ERROR)
        handlers.extend([main_handler, error_handler])

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for HTTP request logging."""

    async def dispatch(self, request: Request, call_next):
        if LOG_DISABLED:
            return await call_next(request)

        request_id = str(uuid4())
        structlog.contextvars.bind_contextvars(request_id=request_id)

        logger.info("request_started", method=request.method, path=request.url.path)

        try:
            response = await call_next(request)
            logger.info("request_finished", status_code=response.status_code)
            return response
        except Exception as e:
            logger.error("request_failed", error=str(e))
            raise
        finally:
            structlog.contextvars.clear_contextvars()


logger = structlog.get_logger()
