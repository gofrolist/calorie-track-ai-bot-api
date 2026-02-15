from fastapi import APIRouter

from ...schemas import HealthResponse

router = APIRouter()


@router.get("/live", response_model=HealthResponse)
async def live():
    return {"status": "ok"}


@router.get("/ready", response_model=HealthResponse)
async def ready():
    return {"status": "ok"}
