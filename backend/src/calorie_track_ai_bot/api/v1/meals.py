from fastapi import APIRouter, HTTPException, Query, Request

from ...schemas import (
    MealCreateFromEstimateRequest,
    MealCreateManualRequest,
    MealCreateResponse,
)
from ...services.db import (
    db_create_meal_from_estimate,
    db_create_meal_from_manual,
    db_delete_meal,
    db_get_meal,
    db_get_meals_by_date,
    db_update_meal,
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


@router.get("/meals")
async def get_meals(
    request: Request, date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """Get meals for a specific date."""
    try:
        # Get user ID from x-user-id header
        telegram_user_id = request.headers.get("x-user-id")

        meals = await db_get_meals_by_date(date, telegram_user_id)
        return meals
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/meals/{meal_id}")
async def get_meal(meal_id: str):
    """Get a specific meal by ID."""
    try:
        meal = await db_get_meal(meal_id)
        if not meal:
            raise HTTPException(404, "Meal not found")
        return meal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.patch("/meals/{meal_id}")
async def update_meal(meal_id: str, updates: dict):
    """Update a meal."""
    try:
        # Validate meal exists
        existing_meal = await db_get_meal(meal_id)
        if not existing_meal:
            raise HTTPException(404, "Meal not found")

        updated_meal = await db_update_meal(meal_id, updates)
        if not updated_meal:
            raise HTTPException(500, "Failed to update meal")

        return updated_meal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.delete("/meals/{meal_id}")
async def delete_meal(meal_id: str):
    """Delete a meal."""
    try:
        # Validate meal exists
        existing_meal = await db_get_meal(meal_id)
        if not existing_meal:
            raise HTTPException(404, "Meal not found")

        success = await db_delete_meal(meal_id)
        if not success:
            raise HTTPException(500, "Failed to delete meal")

        return {"message": "Meal deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e)) from e
