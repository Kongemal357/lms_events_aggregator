from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get(
    "/health/",
    summary="Health check",
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