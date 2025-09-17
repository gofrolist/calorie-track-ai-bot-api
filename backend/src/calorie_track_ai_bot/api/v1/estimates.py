from fastapi import APIRouter, HTTPException

from ...schemas import EstimateQueuedResponse, EstimateResponse, Status
from ...services.config import logger
from ...services.db import db_get_estimate
from ...services.queue import enqueue_estimate_job

router = APIRouter()


@router.post("/photos/{photo_id}/estimate", response_model=EstimateQueuedResponse)
async def estimate_photo(photo_id: str):
    logger.info(f"Requesting estimate for photo_id: {photo_id}")
    try:
        job_id = await enqueue_estimate_job(photo_id)
        logger.info(f"Estimation job enqueued with ID: {job_id} for photo: {photo_id}")
        return EstimateQueuedResponse(estimate_id=job_id, status=Status.queued)
    except Exception as e:
        logger.error(f"Error enqueueing estimation job for photo {photo_id}: {e}", exc_info=True)
        raise HTTPException(500, str(e)) from e


@router.get("/estimates/{estimate_id}", response_model=EstimateResponse)
async def get_estimate(estimate_id: str):
    logger.info(f"Fetching estimate with ID: {estimate_id}")
    try:
        est = await db_get_estimate(estimate_id)
        if not est:
            logger.warning(f"Estimate not found for ID: {estimate_id}")
            raise HTTPException(404, "Not found")
        logger.info(f"Estimate retrieved successfully for ID: {estimate_id}")
        return est
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching estimate {estimate_id}: {e}", exc_info=True)
        raise HTTPException(500, str(e)) from e
