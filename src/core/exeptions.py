class EventNotFound(Exception):
    """Raised when an event is not found in local database."""

    pass


class EventNotPublished(Exception):
    """Raised when an event is not published for registration."""

    pass


class SyncInProgress(Exception):
    """Raised when a sync is already running."""

    pass
