import uuid
from datetime import UTC
from typing import Any

import httpx
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from ..schemas import (
    MealCreateFromEstimateRequest,
    MealCreateManualRequest,
    UIConfiguration,
    UIConfigurationUpdate,
)
from .config import APP_ENV, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL, logger
from .storage import BUCKET_NAME, s3

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


async def db_create_meal_from_estimate(
    data: MealCreateFromEstimateRequest, user_id: str
) -> dict[str, str]:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    mid = str(uuid.uuid4())

    # Get the estimate data to retrieve kcal_mean
    estimate = await db_get_estimate(data.estimate_id)
    if not estimate:
        raise ValueError(f"Estimate not found: {data.estimate_id}")

    # Set kcal_total from estimate unless overridden
    kcal_total = estimate.get("kcal_mean", 0)
    if data.overrides and isinstance(data.overrides, dict):
        kcal_total = data.overrides.get("kcal_total", kcal_total)

    payload = {
        "id": mid,
        "user_id": user_id,
        "meal_date": data.meal_date.isoformat(),
        "meal_type": data.meal_type.value,
        "kcal_total": kcal_total,
        "source": "photo",
        "estimate_id": data.estimate_id,
    }
    sb.table("meals").insert(payload).execute()
    return {"meal_id": mid}


async def _enhance_meal_with_related_data(meal: dict[str, Any]) -> None:
    """Enhance meal data with related estimate and photo information."""
    if not meal.get("estimate_id"):
        # No estimate to fetch - this is a manual meal

        # Add default macros if not present
        if "macros" not in meal:
            meal["macros"] = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

        # Add default corrected status
        if "corrected" not in meal:
            meal["corrected"] = False

        # Ensure updated_at exists for manual meals
        if "updated_at" not in meal and "created_at" in meal:
            meal["updated_at"] = meal["created_at"]
        elif "updated_at" not in meal:
            # If no timestamps exist, create them from current time
            from datetime import datetime

            now = datetime.now(UTC).isoformat()
            meal["created_at"] = now
            meal["updated_at"] = now

        return

    # Fetch related estimate and photo data
    estimate = await db_get_estimate(meal["estimate_id"])
    if not estimate:
        logger.warning(f"Estimate {meal['estimate_id']} not found for meal {meal['id']}")
        meal["photo_url"] = None
        meal["macros"] = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}
        meal["corrected"] = False
        if "updated_at" not in meal and "created_at" in meal:
            meal["updated_at"] = meal["created_at"]
        elif "updated_at" not in meal:
            # If no timestamps exist, create them from current time
            from datetime import datetime

            now = datetime.now(UTC).isoformat()
            meal["created_at"] = now
            meal["updated_at"] = now
        return

    # Get photo data from estimate
    photo = await db_get_photo(estimate["photo_id"])
    if photo and s3:
        try:
            # Generate presigned URL for the photo
            photo_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": photo["tigris_key"]},
                ExpiresIn=3600,  # 1 hour
            )
            meal["photo_url"] = photo_url
        except Exception as e:
            logger.warning(f"Failed to generate photo URL for meal {meal['id']}: {e}")
            meal["photo_url"] = None
    else:
        meal["photo_url"] = None

    # Add macros from estimate (placeholder for now)
    # TODO: Add macronutrient estimation to AI analysis
    meal["macros"] = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

    # Add corrected status
    meal["corrected"] = False  # Meals from estimates are not corrected by user

    # Ensure updated_at exists
    if "updated_at" not in meal and "created_at" in meal:
        meal["updated_at"] = meal["created_at"]
    elif "updated_at" not in meal:
        # If no timestamps exist, create them from current time
        from datetime import datetime

        now = datetime.now(UTC).isoformat()
        meal["created_at"] = now
        meal["updated_at"] = now


async def resolve_user_id(telegram_user_id: str | None) -> str | None:
    """Resolve Telegram user ID to database UUID."""
    if not telegram_user_id:
        return None

    try:
        # Convert string to int for telegram_id lookup
        telegram_id_int = int(telegram_user_id)
        # Get or create user and return the UUID
        return await db_get_or_create_user(telegram_id_int)
    except (ValueError, TypeError):
        # If conversion fails, return None
        logger.warning(f"Invalid telegram_user_id format: {telegram_user_id}")
        return None


async def db_get_meals_by_date(
    meal_date: str, telegram_user_id: str | None = None
) -> list[dict[str, Any]]:
    """Get meals for a specific date with related data."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Resolve Telegram user ID to database UUID
    user_id = await resolve_user_id(telegram_user_id)

    query = sb.table("meals").select("*").eq("meal_date", meal_date)
    if user_id:
        query = query.eq("user_id", user_id)

    res = query.execute()
    meals = res.data if res.data else []

    # Enhance each meal with related data
    for meal in meals:
        await _enhance_meal_with_related_data(meal)

    return meals


async def db_get_meal(meal_id: str) -> dict[str, Any] | None:
    """Get a specific meal by ID with related data."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("meals").select("*").eq("id", meal_id).execute()
    if not res.data:
        return None

    meal = res.data[0]

    # Enhance meal data with related information
    await _enhance_meal_with_related_data(meal)

    return meal


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


async def db_get_daily_summary(
    date: str, telegram_user_id: str | None = None
) -> dict[str, Any] | None:
    """Get daily summary for a specific date."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Resolve Telegram user ID to database UUID
    user_id = await resolve_user_id(telegram_user_id)

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


async def db_get_goal(telegram_user_id: str) -> dict[str, Any] | None:
    """Get user's goal."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Resolve Telegram user ID to database UUID
    user_id = await resolve_user_id(telegram_user_id)
    if not user_id:
        return None

    res = sb.table("goals").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None


async def db_create_or_update_goal(telegram_user_id: str, daily_kcal_target: int) -> dict[str, Any]:
    """Create or update user's goal."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Resolve Telegram user ID to database UUID
    user_id = await resolve_user_id(telegram_user_id)
    if not user_id:
        raise ValueError(f"Could not resolve user ID for telegram_user_id: {telegram_user_id}")

    # Try to find existing goal
    existing = await db_get_goal(telegram_user_id)

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
    start_date: str, end_date: str, telegram_user_id: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get summaries for a date range in a single query."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Resolve Telegram user ID to database UUID
    user_id = await resolve_user_id(telegram_user_id)

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


async def db_get_today_data(date: str, telegram_user_id: str | None = None) -> dict[str, Any]:
    """Get all data needed for the Today page in a single query."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Resolve Telegram user ID to database UUID
    user_id = await resolve_user_id(telegram_user_id)

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


# UI Configuration Database Functions
async def db_get_ui_configuration(user_id: str) -> dict[str, Any] | None:
    """Get UI configuration for a user."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("ui_configurations").select("*").eq("user_id", user_id).execute()
    return res.data[0] if res.data else None


async def db_create_ui_configuration(user_id: str, config: UIConfiguration) -> dict[str, Any]:
    """Create a new UI configuration for a user."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    config_data = {
        "id": config.id,
        "user_id": user_id,
        "environment": config.environment,
        "api_base_url": config.api_base_url,
        "safe_area_top": config.safe_area_top,
        "safe_area_bottom": config.safe_area_bottom,
        "safe_area_left": config.safe_area_left,
        "safe_area_right": config.safe_area_right,
        "theme": config.theme,
        "theme_source": config.theme_source,
        "language": config.language,
        "language_source": config.language_source,
        "features": config.features,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }

    res = sb.table("ui_configurations").insert(config_data).execute()
    return res.data[0] if res.data else config_data


async def db_update_ui_configuration(
    user_id: str, config_id: str, updates: UIConfigurationUpdate
) -> dict[str, Any] | None:
    """Update an existing UI configuration."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Build update data from non-None fields
    update_data = {}

    if updates.environment is not None:
        update_data["environment"] = updates.environment
    if updates.api_base_url is not None:
        update_data["api_base_url"] = updates.api_base_url
    if updates.safe_area_top is not None:
        update_data["safe_area_top"] = updates.safe_area_top
    if updates.safe_area_bottom is not None:
        update_data["safe_area_bottom"] = updates.safe_area_bottom
    if updates.safe_area_left is not None:
        update_data["safe_area_left"] = updates.safe_area_left
    if updates.safe_area_right is not None:
        update_data["safe_area_right"] = updates.safe_area_right
    if updates.theme is not None:
        update_data["theme"] = updates.theme
    if updates.theme_source is not None:
        update_data["theme_source"] = updates.theme_source
    if updates.language is not None:
        update_data["language"] = updates.language
    if updates.language_source is not None:
        update_data["language_source"] = updates.language_source
    if updates.features is not None:
        update_data["features"] = updates.features

    # Always update the updated_at timestamp
    from datetime import datetime

    update_data["updated_at"] = datetime.now(UTC).isoformat()

    res = (
        sb.table("ui_configurations")
        .update(update_data)
        .eq("id", config_id)
        .eq("user_id", user_id)  # Ensure user can only update their own config
        .execute()
    )

    return res.data[0] if res.data else None


async def db_delete_ui_configuration(user_id: str, config_id: str) -> bool:
    """Delete a UI configuration."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = (
        sb.table("ui_configurations")
        .delete()
        .eq("id", config_id)
        .eq("user_id", user_id)  # Ensure user can only delete their own config
        .execute()
    )

    return len(res.data) > 0 if res.data else False


async def db_get_ui_configurations_by_user(user_id: str) -> list[dict[str, Any]]:
    """Get all UI configurations for a user."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = (
        sb.table("ui_configurations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return res.data if res.data else []


async def db_cleanup_old_ui_configurations(user_id: str, keep_count: int = 5) -> int:
    """Clean up old UI configurations, keeping only the most recent ones."""
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    # Get all configurations for the user, ordered by updated_at desc
    all_configs = await db_get_ui_configurations_by_user(user_id)

    if len(all_configs) <= keep_count:
        return 0  # Nothing to clean up

    # Get IDs of configurations to delete (all except the most recent keep_count)
    configs_to_delete = all_configs[keep_count:]
    delete_ids = [config["id"] for config in configs_to_delete]

    if not delete_ids:
        return 0

    # Delete old configurations
    res = (
        sb.table("ui_configurations")
        .delete()
        .in_("id", delete_ids)
        .eq("user_id", user_id)  # Safety check
        .execute()
    )

    deleted_count = len(res.data) if res.data else 0
    logger.info(f"Cleaned up {deleted_count} old UI configurations for user {user_id}")

    return deleted_count
