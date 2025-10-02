from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status

from ...schemas import (
    MealCreateFromEstimateRequest,
    MealCreateManualRequest,
    MealCreateResponse,
    MealsCalendarResponse,
    MealsListResponse,
    MealUpdate,
    MealWithPhotos,
)
from ...services.db import (
    db_create_meal_from_estimate,
    db_create_meal_from_manual,
    db_delete_meal,
    db_get_meal_with_photos,
    db_get_meals_calendar_summary,
    db_get_meals_with_photos,
    db_update_meal_with_macros,
)
from ...utils.error_handling import (
    handle_api_errors,
    validate_user_authentication,
)

router = APIRouter()


@router.post("/meals", response_model=MealCreateResponse)
@handle_api_errors("meal creation")
async def create_meal(
    request: Request, payload: MealCreateManualRequest | MealCreateFromEstimateRequest
):
    if isinstance(payload, MealCreateManualRequest):
        return await db_create_meal_from_manual(payload)

    # For estimate-based meals, we need to get the user_id from headers
    telegram_user_id = validate_user_authentication(request)

    # Resolve telegram_user_id to database user_id
    from ...services.db import resolve_user_id

    user_id = await resolve_user_id(telegram_user_id)
    if not user_id:
        raise HTTPException(400, "User not found")

    return await db_create_meal_from_estimate(payload, user_id)


@router.get("/meals", response_model=MealsListResponse)
@handle_api_errors("meal retrieval")
async def get_meals(
    request: Request,
    date: str | None = Query(None, description="Specific date (YYYY-MM-DD)"),
    start_date: str | None = Query(None, description="Start date for range (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="End date for range (YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of meals to return"),
) -> MealsListResponse:
    """Get meals with photos and macronutrients.

    Feature: 003-update-logic-for (Multi-photo support)
    Supports:
    - Single date query: ?date=2025-09-30
    - Date range query: ?start_date=2025-09-23&end_date=2025-09-30
    - Default: today's meals
    """
    # Get user ID from request (assumes auth middleware sets this)
    telegram_user_id = validate_user_authentication(request)

    from ...services.db import resolve_user_id

    user_id = await resolve_user_id(telegram_user_id)
    if not user_id:
        raise HTTPException(status_code=401, detail="User not found")

    # Parse date parameters
    query_date = None
    query_start = None
    query_end = None

    try:
        if date:
            query_date = datetime.fromisoformat(date).date()
        elif start_date and end_date:
            query_start = datetime.fromisoformat(start_date).date()
            query_end = datetime.fromisoformat(end_date).date()
        else:
            # Default to today
            query_date = datetime.now().date()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid date format: {e}"
        ) from None

    # Get meals with photos
    meals = await db_get_meals_with_photos(
        user_id=UUID(user_id),
        query_date=query_date,
        start_date=query_start,
        end_date=query_end,
        limit=limit,
    )

    return MealsListResponse(meals=meals, total=len(meals))


@router.get("/meals/calendar", response_model=MealsCalendarResponse)
async def get_meals_calendar(
    request: Request,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
) -> MealsCalendarResponse:
    """Get daily meal summaries for calendar view.

    Feature: 003-update-logic-for (Calendar navigation)
    Returns aggregated nutrition data by date.
    """
    try:
        # Validate authentication
        telegram_user_id = request.headers.get("x-user-id")
        if not telegram_user_id:
            raise HTTPException(status_code=401, detail="User ID required")

        from ...services.db import resolve_user_id

        user_id = await resolve_user_id(telegram_user_id)
        if not user_id:
            raise HTTPException(status_code=401, detail="User not found")

        # Parse dates
        query_start = datetime.fromisoformat(start_date).date()
        query_end = datetime.fromisoformat(end_date).date()

        # Validate date range (max 1 year)
        if (query_end - query_start).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 1 year")

        # Get calendar summary
        calendar_data = await db_get_meals_calendar_summary(
            user_id=UUID(user_id), start_date=query_start, end_date=query_end
        )

        return MealsCalendarResponse(dates=calendar_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e!s}") from e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/meals/{meal_id}", response_model=MealWithPhotos)
async def get_meal(meal_id: str, request: Request) -> MealWithPhotos:
    """Get a specific meal with photos and macronutrients.

    Feature: 003-update-logic-for (Multi-photo support)
    """
    try:
        # Validate user ownership
        telegram_user_id = request.headers.get("x-user-id")
        if not telegram_user_id:
            raise HTTPException(status_code=401, detail="User ID required")

        # Resolve telegram_user_id to database user_id
        from ...services.db import resolve_user_id

        user_id = await resolve_user_id(telegram_user_id)
        if not user_id:
            raise HTTPException(status_code=401, detail="User not found")

        try:
            meal = await db_get_meal_with_photos(UUID(meal_id))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid meal ID format") from None

        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")

        # Verify ownership
        if str(meal.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You do not own this meal")

        return meal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/meals/{meal_id}", response_model=MealWithPhotos)
async def update_meal(meal_id: str, payload: MealUpdate, request: Request) -> MealWithPhotos:
    """Update meal description or macronutrients.

    Feature: 003-update-logic-for (Meal editing)
    Automatically recalculates calories from macros if updated.
    """
    try:
        # Validate authentication
        telegram_user_id = request.headers.get("x-user-id")
        if not telegram_user_id:
            raise HTTPException(status_code=401, detail="User ID required")

        from ...services.db import resolve_user_id

        user_id = await resolve_user_id(telegram_user_id)
        if not user_id:
            raise HTTPException(status_code=401, detail="User not found")

        # Validate meal exists and ownership
        try:
            existing_meal = await db_get_meal_with_photos(UUID(meal_id))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid meal ID format") from None

        if not existing_meal:
            raise HTTPException(status_code=404, detail="Meal not found")

        if str(existing_meal.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You do not own this meal")

        # Update meal with macronutrient recalculation
        updated_meal = await db_update_meal_with_macros(meal_id=UUID(meal_id), updates=payload)

        if not updated_meal:
            raise HTTPException(status_code=500, detail="Failed to update meal")

        return updated_meal

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: str, request: Request):
    """Delete a meal and update daily summary.

    Feature: 003-update-logic-for (Meal management)
    Cascades to photos and recalculates daily stats.
    """
    try:
        # Validate authentication
        telegram_user_id = request.headers.get("x-user-id")
        if not telegram_user_id:
            raise HTTPException(status_code=401, detail="User ID required")

        from ...services.db import resolve_user_id

        user_id = await resolve_user_id(telegram_user_id)
        if not user_id:
            raise HTTPException(status_code=401, detail="User not found")

        # Validate meal exists and ownership
        try:
            existing_meal = await db_get_meal_with_photos(UUID(meal_id))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid meal ID format") from None

        if not existing_meal:
            raise HTTPException(status_code=404, detail="Meal not found")

        if str(existing_meal.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You do not own this meal")

        # Delete meal (cascades to photos, updates daily summary)
        success = await db_delete_meal(meal_id)  # db_delete_meal expects str
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete meal")

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
