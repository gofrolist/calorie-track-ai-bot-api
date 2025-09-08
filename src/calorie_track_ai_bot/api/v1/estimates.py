from fastapi import APIRouter, HTTPException

from ...schemas import EstimateQueuedResponse, EstimateResponse, Status
from ...services.db import db_get_estimate
from ...services.queue import enqueue_estimate_job

router = APIRouter()


@router.post("/photos/{photo_id}/estimate", response_model=EstimateQueuedResponse)
async def estimate_photo(photo_id: str):
    try:
        job_id = await enqueue_estimate_job(photo_id)
        return EstimateQueuedResponse(estimate_id=job_id, status=Status.queued)
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/estimates/{estimate_id}", response_model=EstimateResponse)
async def get_estimate(estimate_id: str):
    try:
        est = await db_get_estimate(estimate_id)
        if not est:
            raise HTTPException(404, "Not found")
        return est
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)) from e
