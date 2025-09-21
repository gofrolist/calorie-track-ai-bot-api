import uuid
from typing import Any

import httpx
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from ..schemas import MealCreateFromEstimateRequest, MealCreateManualRequest
from .config import APP_ENV, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL, logger

# Initialize Supabase client only if configuration is available
sb: Any | None = None

if SUPABASE_URL is not None and SUPABASE_SERVICE_ROLE_KEY is not None:
    # Create a custom httpx client to avoid deprecation warnings
    httpx_client = httpx.Client(timeout=httpx.Timeout(120.0))

    # Create Supabase client with service role key to bypass RLS
    options = SyncClientOptions(httpx_client=httpx_client)
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, options)
elif APP_ENV == "dev":
    # In development mode, allow missing Supabase config
    print("WARNING: Supabase configuration not set. Database functionality will be disabled.")
    print("To enable database operations, set the following environment variables:")
    print("- SUPABASE_URL")
    print("- SUPABASE_SERVICE_ROLE_KEY")
else:
    raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")


async def db_create_photo(tigris_key: str, user_id: str | None = None) -> str:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    logger.debug(f"Creating photo record with tigris_key: {tigris_key}, user_id: {user_id}")
    pid = str(uuid.uuid4())
    photo_data = {"id": pid, "tigris_key": tigris_key}
    if user_id:
        photo_data["user_id"] = user_id

    sb.table("photos").insert(photo_data).execute()
    logger.info(f"Photo record created with ID: {pid}")
    return pid


async def db_get_or_create_user(
    telegram_id: int, handle: str | None = None, locale: str = "en"
) -> str:
    """Get existing user or create new one based on telegram_id."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    logger.debug(f"Looking up user with telegram_id: {telegram_id}")

    # Try to find existing user
    res = sb.table("users").select("*").eq("telegram_id", telegram_id).execute()

    if res.data:
        user_id = res.data[0]["id"]
        logger.info(f"Found existing user with ID: {user_id}")
        return user_id

    # Create new user
    user_id = str(uuid.uuid4())
    user_data = {"id": user_id, "telegram_id": telegram_id, "handle": handle, "locale": locale}

    logger.info(f"Creating new user with ID: {user_id}, telegram_id: {telegram_id}")
    sb.table("users").insert(user_data).execute()
    return user_id


async def db_save_estimate(photo_id: str, est: dict[str, Any]) -> str:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    eid = str(uuid.uuid4())

    # Insert estimate data directly - database now has 'items' column
    estimate_data = {"id": eid, "photo_id": photo_id, **est}

    sb.table("estimates").insert(estimate_data).execute()
    return eid


async def db_get_estimate(estimate_id: str) -> dict[str, Any] | None:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("estimates").select("*").eq("id", estimate_id).execute()
    return res.data[0] if res.data else None


async def db_get_photo(photo_id: str) -> dict[str, Any] | None:
    """Get photo record by ID."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("photos").select("*").eq("id", photo_id).execute()
    return res.data[0] if res.data else None


async def db_get_user(user_id: str) -> dict[str, Any] | None:
    """Get user record by ID."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("users").select("*").eq("id", user_id).execute()
    return res.data[0] if res.data else None


async def db_create_meal_from_manual(data: MealCreateManualRequest) -> dict[str, str]:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    mid = str(uuid.uuid4())
    payload = {
        "id": mid,
        "user_id": None,
        "meal_date": data.meal_date.isoformat(),
        "meal_type": data.meal_type.value,
        "kcal_total": data.kcal_total,
        "source": "manual",
    }
    sb.table("meals").insert(payload).execute()
    return {"meal_id": mid}


async def db_create_meal_from_estimate(data: MealCreateFromEstimateRequest) -> dict[str, str]:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    mid = str(uuid.uuid4())
    kcal_total = None
    if data.overrides and isinstance(data.overrides, dict):
        kcal_total = data.overrides.get("kcal_total")
    payload = {
        "id": mid,
        "user_id": None,
        "meal_date": data.meal_date.isoformat(),
        "meal_type": data.meal_type.value,
        "kcal_total": kcal_total if kcal_total is not None else 0,
        "source": "photo",
        "estimate_id": data.estimate_id,
    }
    sb.table("meals").insert(payload).execute()
    return {"meal_id": mid}


async def db_get_meals_by_date(meal_date: str, user_id: str | None = None) -> list[dict[str, Any]]:
    """Get meals for a specific date."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    query = sb.table("meals").select("*").eq("meal_date", meal_date)
    if user_id:
        query = query.eq("user_id", user_id)

    res = query.execute()
    return res.data if res.data else []


async def db_get_meal(meal_id: str) -> dict[str, Any] | None:
    """Get a specific meal by ID."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("meals").select("*").eq("id", meal_id).execute()
    return res.data[0] if res.data else None


async def db_update_meal(meal_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a meal with the given updates."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("meals").update(updates).eq("id", meal_id).execute()
    return res.data[0] if res.data else None


async def db_delete_meal(meal_id: str) -> bool:
    """Delete a meal by ID."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("meals").delete().eq("id", meal_id).execute()
    return len(res.data) > 0 if res.data else False


async def db_get_daily_summary(date: str, user_id: str | None = None) -> dict[str, Any] | None:
    """Get daily summary for a specific date."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    query = sb.table("meals").select("kcal_total").eq("meal_date", date)
    if user_id:
        query = query.eq("user_id", user_id)

    res = query.execute()
    meals = res.data if res.data else []

    # Calculate totals
    total_kcal = sum(meal.get("kcal_total", 0) for meal in meals)

    # Since macros column doesn't exist in the current schema, return zeros
    macro_totals = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

    return {
        "user_id": user_id,
        "date": date,
        "kcal_total": total_kcal,
        "macros_totals": macro_totals,
    }


def db_get_goal(user_id: str) -> dict[str, Any] | None:
    """Get user's goal."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("goals").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None


def db_create_or_update_goal(user_id: str, daily_kcal_target: int) -> dict[str, Any]:
    """Create or update user's goal."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Try to find existing goal
    existing = db_get_goal(user_id)

    if existing:
        # Update existing goal
        res = (
            sb.table("goals")
            .update({"daily_kcal_target": daily_kcal_target, "updated_at": "now()"})
            .eq("id", existing["id"])
            .execute()
        )
        if res.data:
            return res.data[0]
        else:
            # Fallback to creating new goal if update failed
            goal_id = str(uuid.uuid4())
            goal_data = {"id": goal_id, "user_id": user_id, "daily_kcal_target": daily_kcal_target}
            sb.table("goals").insert(goal_data).execute()
            return goal_data
    else:
        # Create new goal
        goal_id = str(uuid.uuid4())
        goal_data = {"id": goal_id, "user_id": user_id, "daily_kcal_target": daily_kcal_target}
        sb.table("goals").insert(goal_data).execute()
        return goal_data


async def db_get_summaries_by_date_range(
    start_date: str, end_date: str, user_id: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get summaries for a date range in a single query."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    query = (
        sb.table("meals")
        .select("meal_date, kcal_total")
        .gte("meal_date", start_date)
        .lte("meal_date", end_date)
    )
    if user_id:
        query = query.eq("user_id", user_id)

    res = query.execute()
    meals = res.data if res.data else []

    # Group meals by date and calculate summaries
    summaries = {}
    for meal in meals:
        date = meal["meal_date"]
        if date not in summaries:
            summaries[date] = {
                "user_id": user_id,
                "date": date,
                "kcal_total": 0,
                "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
            }

        summaries[date]["kcal_total"] += meal.get("kcal_total", 0)

    return summaries


async def db_get_today_data(date: str, user_id: str | None = None) -> dict[str, Any]:
    """Get all data needed for the Today page in a single query."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Get all meals for the date
    query = sb.table("meals").select("*").eq("meal_date", date)
    if user_id:
        query = query.eq("user_id", user_id)

    res = query.execute()
    meals = res.data if res.data else []

    # Calculate daily summary
    daily_summary = {
        "user_id": user_id,
        "date": date,
        "kcal_total": sum(meal.get("kcal_total", 0) for meal in meals),
        "macros_totals": {
            "protein_g": 0,  # Will be calculated when macros column exists
            "fat_g": 0,
            "carbs_g": 0,
        },
    }

    return {"meals": meals, "daily_summary": daily_summary}
