from fastapi import APIRouter, HTTPException

from ...schemas import (
    MealCreateFromEstimateRequest,
    MealCreateManualRequest,
    MealCreateResponse,
)
from ...services.db import (
    db_create_meal_from_estimate,
    db_create_meal_from_manual,
)

router = APIRouter()


@router.post("/meals", response_model=MealCreateResponse)
async def create_meal(payload: MealCreateManualRequest | MealCreateFromEstimateRequest):
    try:
        if isinstance(payload, MealCreateManualRequest):
            return await db_create_meal_from_manual(payload)
        return await db_create_meal_from_estimate(payload)
    except Exception as e:
        raise HTTPException(500, str(e)) from e
