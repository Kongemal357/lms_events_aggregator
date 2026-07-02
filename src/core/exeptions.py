class EventNotFound(Exception):
    """Raised when an event is not found in local database."""

    pass


class EventNotPublished(Exception):
    """Raised when an event is not published for registration."""

    pass


class SyncInProgress(Exception):
    """Raised when a sync is already running."""

    pass


class RegistrationDeadlinePassed(Exception):
    """Raised when trying to register after the registration deadline."""

    pass


class SeatUnavailable(Exception):
    """Raised when the requested seat is already taken."""

    pass


class TicketNotFound(Exception):
    """Raised when a ticket is not found or already cancelled."""

    pass


class EventAlreadyPassed(Exception):
    """Raised when trying to cancel a ticket for a past event."""

    pass
