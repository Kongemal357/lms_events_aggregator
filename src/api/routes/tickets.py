from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from src.api.dependencies import get_cancel_ticket_usecase, get_create_ticket_usecase
from src.core.exeptions import (
    EventAlreadyPassed,
    EventNotFound,
    EventNotPublished,
    RegistrationDeadlinePassed,
    SeatUnavailable,
    TicketNotFound,
)
from src.core.logging import logger
from src.core.schemas import CancelResponse, TicketRequest, TicketResponse

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    summary="Register on an event",
    description="Register a participant on an event with seat selection.",
)
async def create_ticket(
    body: TicketRequest,
    usecase=Depends(get_create_ticket_usecase),
):
    try:
        return await usecase.do(
            event_id=body.event_id,
            first_name=body.first_name,
            last_name=body.last_name,
            email=body.email,
            seat=body.seat,
        )
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except RegistrationDeadlinePassed:
        raise HTTPException(status_code=400, detail="Registration deadline passed")
    except SeatUnavailable:
        raise HTTPException(status_code=400, detail="Seat is already taken")
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Data integrity error")
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        logger.exception("create_ticket_failed")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{ticket_id}",
    response_model=CancelResponse,
    summary="Cancel registration",
    description="Cancel a registration by ticket ID.",
)
async def cancel_ticket(
    ticket_id: str,
    usecase=Depends(get_cancel_ticket_usecase),
):
    try:
        return await usecase.do(ticket_id)
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except EventAlreadyPassed:
        raise HTTPException(status_code=400, detail="Event already passed")
    except HTTPException:
        raise
    except Exception:
        logger.exception("cancel_ticket_failed")
        raise HTTPException(status_code=500, detail="Internal server error")
