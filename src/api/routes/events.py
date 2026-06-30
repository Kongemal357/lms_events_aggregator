from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from src.api.dependencies import get_event_detail_usecase, get_events_usecase
from src.core.schemas import EventDetailResponse, EventListResponse
from src.core.usecases.get_event_detail import EventNotFound

router = APIRouter(prefix="/events", tags=["events"])


@router.get(
    "/",
    response_model=EventListResponse,
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
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")


@router.get(
    "/{event_id}/",
    response_model=EventDetailResponse,
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
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
