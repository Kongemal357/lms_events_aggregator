import uuid
from datetime import datetime

from pydantic import BaseModel, model_validator


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


# ─── Sync ───────────────────────────────────────────
class SyncTriggerResponse(BaseModel):
    """Response after triggering a manual sync.

    Returned by POST /api/sync/trigger/.
    """

    message: str