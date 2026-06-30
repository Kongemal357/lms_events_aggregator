import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Event(Base):
    """Cached event synced from Events Provider API.

    Place fields are denormalized since the aggregator only reads them
    and never updates places independently.
    """

    __tablename__ = "events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    number_of_visitors: Mapped[int] = mapped_column(Integer, default=0)

    # Denormalized place data
    place_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    place_name: Mapped[str] = mapped_column(String, nullable=False)
    place_city: Mapped[str] = mapped_column(String, nullable=False)
    place_address: Mapped[str] = mapped_column(String, nullable=False)
    place_seats_pattern: Mapped[str] = mapped_column(String, nullable=False)

    # Sync metadata from provider
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    provider_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Local tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="event", lazy="selectin"
    )


class Ticket(Base):
    """Local record of a registration made via Events Provider API.

    ticket_id comes from the provider and is NOT unique — it can be reused
    after cancellation. Use (ticket_id, email) to identify active registrations.
    """

    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[str] = mapped_column(String, nullable=False)
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("events.id"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    seat: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    event: Mapped["Event"] = relationship("Event", back_populates="tickets")


class SyncMetadata(Base):
    """Single-row table storing incremental sync state.

    last_changed_at is passed to the provider as the changed_at parameter.
    sync_status prevents concurrent sync runs.
    """

    __tablename__ = "sync_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    last_changed_at: Mapped[str] = mapped_column(String, nullable=False, default="2000-01-01")
    last_sync_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_sync_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_status: Mapped[str] = mapped_column(String, nullable=False, default="idle")
