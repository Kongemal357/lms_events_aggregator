import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ─── error_handler ───────────────────────────────────────────
class ErrorResponse(BaseModel):
    """Standard error response, matching Events Provider API format."""

    detail: str


error_dict_400_404_409_500: dict = {
    400: {"model": ErrorResponse, "description": "Bad request or validation error"},
    404: {"model": ErrorResponse, "description": "Not found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    500: {"model": ErrorResponse, "description": "Internal server error"},
}


# ─── Place ───────────────────────────────────────────
class PlaceBriefSchema(BaseModel):
    """Place in event list — without seats_pattern."""

    id: uuid.UUID
    name: str
    city: str
    address: str

    model_config = {"from_attributes": True}


class PlaceDetailSchema(PlaceBriefSchema):
    """Place in event details — includes seats_pattern."""

    seats_pattern: str

    model_config = {"from_attributes": True}


# ─── Event ───────────────────────────────────────────
class EventSchema(BaseModel):
    """Event in paginated list.

    Returned in GET /api/events/ inside EventListResponse.results.
    """

    id: uuid.UUID
    name: str
    place: PlaceBriefSchema
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def flatten_place(cls, data):
        """Build nested PlaceBrief from denormalized ORM fields."""
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "name": data.name,
            "place": {
                "id": data.place_id,
                "name": data.place_name,
                "city": data.place_city,
                "address": data.place_address,
            },
            "event_time": data.event_time,
            "registration_deadline": data.registration_deadline,
            "status": data.status,
            "number_of_visitors": data.number_of_visitors,
        }


class EventDetailResponse(EventSchema):
    """Event details.

    Returned by GET /api/events/{event_id}/.
    Differs from EventSchema by including seats_pattern in place.
    """

    place: PlaceDetailSchema

    @model_validator(mode="before")
    @classmethod
    def flatten_place(cls, data):
        """Build nested PlaceDetail from denormalized ORM fields."""
        if isinstance(data, dict):
            return data
        return {
            "id": data.id,
            "name": data.name,
            "place": {
                "id": data.place_id,
                "name": data.place_name,
                "city": data.place_city,
                "address": data.place_address,
                "seats_pattern": data.place_seats_pattern,
            },
            "event_time": data.event_time,
            "registration_deadline": data.registration_deadline,
            "status": data.status,
            "number_of_visitors": data.number_of_visitors,
        }


class EventListResponse(BaseModel):
    """Paginated list of events.

    Returned by GET /api/events/.
    """

    count: int
    next: str | None
    previous: str | None
    results: list[EventSchema]


# ─── Seats ───────────────────────────────────────────
class SeatsResponse(BaseModel):
    """Available seats for an event.

    Returned by GET /api/events/{event_id}/seats/.
    """

    event_id: uuid.UUID
    available_seats: list[str]


# ─── Tickets ─────────────────────────────────────────
class TicketRequest(BaseModel):
    """Request body for creating a ticket.

    Used by POST /api/tickets/.
    """

    event_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    seat: str

    @field_validator("first_name", "last_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Validate that name fields are not empty or whitespace-only."""
        if not v.strip():
            raise ValueError("must not be empty")
        return v.strip()

    @field_validator("seat")
    @classmethod
    def valid_seat_format(cls, v: str) -> str:
        """Validate seat format (e.g. 'A15')."""
        if not v or len(v) < 2:
            raise ValueError("invalid seat format")
        return v.strip().upper()


class TicketResponse(BaseModel):
    """Response after successful registration.

    Returned by POST /api/tickets/.
    """

    ticket_id: str


class CancelRequest(BaseModel):
    """Request body for cancelling a ticket.

    Used by DELETE /api/tickets/{ticket_id}/.
    """

    ticket_id: str


class CancelResponse(BaseModel):
    """Response after successful cancellation.

    Returned by DELETE /api/tickets/{ticket_id}/.
    """

    success: bool


# ─── Sync ───────────────────────────────────────────
class SyncTriggerResponse(BaseModel):
    """Response after triggering a manual sync.

    Returned by POST /api/sync/trigger/.
    """

    message: str
