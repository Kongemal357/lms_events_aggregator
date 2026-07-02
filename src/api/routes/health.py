from fastapi import APIRouter

from src.core.schemas import error_dict_400_404_409_500

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    responses=error_dict_400_404_409_500,
    description="""
    Returns the health status of the service.

    Used by the platform for monitoring and automated deployment verification.
    """,
)
async def health():
    """Return service health status.

    :return: Simple JSON with status "ok".
    :rtype: dict
    """
    return {"status": "ok"}
