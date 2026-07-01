from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from src.api.dependencies import get_event_detail_usecase, get_events_usecase, get_seats_usecase
from src.core.exeptions import EventNotFound, EventNotPublished
from src.core.logging import logger
from src.core.schemas import (
    EventDetailResponse,
    EventListResponse,
    SeatsResponse,
    error_dict_400_404_409_422_500,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get(
    "",
    response_model=EventListResponse,
    responses=error_dict_400_404_409_422_500,
    summary="List events",
    description="""
    Returns a paginated list of events from the local database.
    Supports optional filtering by date. Data is served from local cache
    without calling the external Events Provider API.
    """,
)
async def list_events(
    request: Request,
    date_from: str | None = Query(
        None,
        description="Filter events starting after this date (YYYY-MM-DD format).",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number, 1-based.",
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of events per page.",
    ),
    usecase=Depends(get_events_usecase),
):
    """Return paginated list of events with optional date filter.

    :param request: Incoming HTTP request, used to extract base URL for
        next/previous pagination links.
    :param date_from: Optional date string in YYYY-MM-DD format. When set,
        only events with event_time >= this date are returned.
    :param page: Page number, starting from 1.
    :param page_size: Maximum number of events per page, between 1 and 100.
    :param usecase: GetEventsUsecase dependency.

    :return: Paginated event list with count, next/previous links,
        and results array.
    :rtype: EventListResponse

    :raises HTTPException 500: If a database error occurs during query execution.
    """
    try:
        base_url = str(request.base_url).rstrip("/")
        parsed_date = datetime.fromisoformat(date_from) if date_from else None
        return await usecase.do(
            date_from=parsed_date,
            page=page,
            page_size=page_size,
            base_url=base_url,
        )
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        logger.exception("unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{event_id}",
    response_model=EventDetailResponse,
    responses=error_dict_400_404_409_422_500,
    summary="Get event details",
    description="""
    Returns detailed information about a specific event from the local database.
    Includes the seats_pattern field in the place object.
    """,
)
async def get_event(
    event_id: str = Path(
        ...,
        title="Event UUID",
        description="The UUID of the event to retrieve. Must be a valid UUID v4 format.",
    ),
    usecase=Depends(get_event_detail_usecase),
):
    """Return event details by ID from local database.

    :param event_id: UUID of the event to retrieve.
    :param usecase: GetEventDetailUsecase dependency.

    :return: Event details including place with seats_pattern.
    :rtype: EventDetailResponse

    :raises HTTPException 404: If the event is not found in the database
        or the UUID format is invalid.
    :raises HTTPException 500: If a database error occurs.
    """
    try:
        return await usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        logger.exception("unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{event_id}/seats",
    response_model=SeatsResponse,
    responses=error_dict_400_404_409_422_500,
    summary="Get available seats",
    description="""
    Returns a list of available seats for a specific event.
    Data is fetched from the Events Provider API and cached for 30 seconds.
    Only works for events with status "published".
    """,
)
async def get_seats(
    event_id: str = Path(
        ...,
        title="Event UUID",
        description="The UUID of the event to get seats for.",
    ),
    usecase=Depends(get_seats_usecase),
):
    """Return available seats for an event.

    :param event_id: UUID of the event.
    :param usecase: GetSeatsUsecase dependency.

    :return: List of available seat IDs.
    :rtype: SeatsResponse

    :raises HTTPException 404: If the event is not found.
    :raises HTTPException 400: If the event is not published.
    :raises HTTPException 500: If a network or database error occurs.
    """
    try:
        return await usecase.do(event_id)
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        logger.exception("unexpected_error")
        raise HTTPException(status_code=500, detail="Internal server error")
