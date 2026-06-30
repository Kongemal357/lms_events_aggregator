from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from src.api.dependencies import get_sync_usecase
from src.core.schemas import SyncTriggerResponse
from src.core.usecases.sync_events import SyncInProgress

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post(
    "/trigger",
    response_model=SyncTriggerResponse,
    summary="Trigger manual sync",
    description="""
    Manually triggers a full synchronization of events from the
    Events Provider API into the local database.

    If a sync is already in progress (status "running" and started
    less than 10 minutes ago), the request is rejected.
    """,
)
async def trigger_sync(usecase=Depends(get_sync_usecase)):
    """Trigger a manual synchronization of events from the external provider.

    :param usecase: SyncEventsUsecase dependency.

    :return: Message with the number of synced events.
    :rtype: SyncTriggerResponse

    :raises HTTPException 409: If a sync is already in progress.
    :raises HTTPException 500: If a database or network error occurs.
    """
    try:
        synced_count = await usecase.do()
        return SyncTriggerResponse(message=f"Sync completed, {synced_count} events synced")
    except SyncInProgress as e:
        raise HTTPException(status_code=409, detail=str(e))
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
