import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import httpx
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from ..schemas import (
    MealCreateFromEstimateRequest,
    MealCreateManualRequest,
    MealPhotoInfo,
    UIConfiguration,
    UIConfigurationUpdate,
)
from .config import APP_ENV, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL, logger
from .storage import BUCKET_NAME, s3

# User ID cache to reduce database queries
_user_id_cache: dict[str, str] = {}
_user_cache_ttl: dict[str, datetime] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

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


async def db_create_photo(
    tigris_key: str,
    user_id: str | None = None,
    display_order: int = 0,
    media_group_id: str | None = None,
) -> str:
    """Create a photo record in the database.

    Args:
        tigris_key: Storage key for the photo
        user_id: UUID of the user who owns the photo
        display_order: Position in carousel (0-4)
        media_group_id: Telegram media group ID for grouped photos

    Returns:
        Photo ID (UUID)
    """
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    logger.debug(
        f"Creating photo record: tigris_key={tigris_key}, user_id={user_id}, "
        f"display_order={display_order}, media_group_id={media_group_id}"
    )
    pid = str(uuid.uuid4())

    # Build photo data with fallback for missing columns
    photo_data: dict[str, Any] = {"id": pid, "tigris_key": tigris_key}

    # Only include columns that exist in the current schema
    try:
        # Try with display_order first (new schema)
        photo_data["display_order"] = display_order
        if user_id:
            photo_data["user_id"] = user_id
        if media_group_id:
            photo_data["media_group_id"] = media_group_id

        sb.table("photos").insert(photo_data).execute()
        logger.info(f"Photo record created with ID: {pid}")
        return pid

    except Exception as e:
        # If display_order column doesn't exist, retry without it
        if "display_order" in str(e) or "PGRST204" in str(e):
            logger.warning("display_order column not found, falling back to legacy schema")
            photo_data = {"id": pid, "tigris_key": tigris_key}
            if user_id:
                photo_data["user_id"] = user_id

            sb.table("photos").insert(photo_data).execute()
            logger.info(f"Photo record created with ID: {pid} (legacy schema)")
            return pid
        else:
            # Re-raise other errors
            raise


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


async def db_save_estimate(
    photo_id: str, est: dict[str, Any], photo_ids: list[str] | None = None
) -> str:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    eid = str(uuid.uuid4())

    # Insert estimate data directly - database now has 'items' column
    estimate_data = {"id": eid, "photo_id": photo_id, **est}

    # Add photo_ids array if provided (for multi-photo estimates)
    # Try to include photo_ids, but handle gracefully if column doesn't exist
    if photo_ids:
        estimate_data["photo_ids"] = photo_ids

    try:
        sb.table("estimates").insert(estimate_data).execute()
        return eid
    except Exception as e:
        # If photo_ids column doesn't exist, retry without it
        if "photo_ids" in str(e) and "column" in str(e).lower():
            logger.warning(f"photo_ids column not available, saving estimate without it: {e}")
            estimate_data.pop("photo_ids", None)
            sb.table("estimates").insert(estimate_data).execute()
            return eid
        else:
            # Re-raise if it's a different error
            raise


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

    # Extract macronutrients from estimate
    macronutrients = estimate.get("macronutrients", {})
    protein_grams = macronutrients.get("protein", 0)
    carbs_grams = macronutrients.get("carbs", 0)
    fats_grams = macronutrients.get("fats", 0)

    # Apply overrides if provided
    if data.overrides and isinstance(data.overrides, dict):
        protein_grams = data.overrides.get("protein_grams", protein_grams)
        carbs_grams = data.overrides.get("carbs_grams", carbs_grams)
        fats_grams = data.overrides.get("fats_grams", fats_grams)

    payload = {
        "id": mid,
        "user_id": user_id,
        "meal_date": data.meal_date.isoformat(),
        "meal_type": data.meal_type.value,
        "kcal_total": kcal_total,
        "protein_grams": protein_grams,
        "carbs_grams": carbs_grams,
        "fats_grams": fats_grams,
        "source": "photo",
        "estimate_id": data.estimate_id,
    }
    sb.table("meals").insert(payload).execute()

    # Link photos to the meal by updating their meal_id
    # The estimate should contain photo_ids array for multi-photo estimates
    photo_ids = estimate.get("photo_ids", [])
    if not photo_ids:
        # Fallback: use single photo_id if photo_ids array is not available
        single_photo_id = estimate.get("photo_id")
        if single_photo_id:
            photo_ids = [single_photo_id]

    if photo_ids:
        # Update photos with meal_id and display_order
        for i, photo_id in enumerate(photo_ids[:5]):  # Max 5 photos
            sb.table("photos").update({"meal_id": mid, "display_order": i}).eq(
                "id", photo_id
            ).execute()
        logger.info(f"Linked {len(photo_ids)} photos to meal {mid}")
    else:
        logger.warning(f"No photo_ids found in estimate {data.estimate_id}")

    return {"meal_id": mid}


def _generate_meal_description(estimate: dict[str, Any]) -> str:
    """Generate a meal description from AI estimate items."""
    if not estimate or "items" not in estimate:
        return "No description available"

    items = estimate["items"]
    if not items or not isinstance(items, list):
        return "No description available"

    # Generate description from food items
    descriptions = []
    for item in items:
        if isinstance(item, dict) and "label" in item:
            descriptions.append(item["label"])

    if descriptions:
        if len(descriptions) == 1:
            return descriptions[0]
        elif len(descriptions) == 2:
            return f"{descriptions[0]} and {descriptions[1]}"
        else:
            return f"{', '.join(descriptions[:-1])}, and {descriptions[-1]}"

    return "No description available"


async def _enhance_meal_with_related_data(meal: dict[str, Any]) -> None:
    """Enhance meal data with related estimate and photo information."""
    if not meal.get("estimate_id"):
        # No estimate to fetch - this is a manual meal

        # Add default macros if not present
        if "macros" not in meal:
            meal["macros"] = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

        # Add default description for manual meals
        if "description" not in meal:
            meal["description"] = "Manual entry"

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

    # Add macros from database (already stored during meal creation)
    meal["macros"] = {
        "protein_g": meal.get("protein_grams", 0) or 0,
        "fat_g": meal.get("fats_grams", 0) or 0,
        "carbs_g": meal.get("carbs_grams", 0) or 0,
    }

    # Generate description from AI estimate items
    meal["description"] = _generate_meal_description(estimate)

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
    """Resolve Telegram user ID to database UUID with caching."""
    if not telegram_user_id:
        return None

    try:
        # Clean up expired cache entries periodically
        _cleanup_user_cache()

        # Check cache first
        current_time = datetime.now(UTC)
        if telegram_user_id in _user_id_cache:
            # Check if cache entry is still valid
            if (
                telegram_user_id in _user_cache_ttl
                and _user_cache_ttl[telegram_user_id] > current_time
            ):
                logger.debug(f"User ID cache hit for telegram_id: {telegram_user_id}")
                return _user_id_cache[telegram_user_id]
            else:
                # Cache expired, remove it
                _user_id_cache.pop(telegram_user_id, None)
                _user_cache_ttl.pop(telegram_user_id, None)

        # Convert string to int for telegram_id lookup
        telegram_id_int = int(telegram_user_id)
        # Get or create user and return the UUID
        user_id = await db_get_or_create_user(telegram_id_int)

        # Cache the result
        if user_id:
            _user_id_cache[telegram_user_id] = user_id
            _user_cache_ttl[telegram_user_id] = current_time + timedelta(seconds=CACHE_TTL_SECONDS)
            logger.debug(f"User ID cached for telegram_id: {telegram_user_id}")

        return user_id
    except (ValueError, TypeError):
        # If conversion fails, return None
        logger.warning(f"Invalid telegram_user_id format: {telegram_user_id}")
        return None


def _cleanup_user_cache():
    """Clean up expired cache entries to prevent memory leaks."""
    current_time = datetime.now(UTC)
    expired_keys = [key for key, expiry in _user_cache_ttl.items() if expiry <= current_time]

    for key in expired_keys:
        _user_id_cache.pop(key, None)
        _user_cache_ttl.pop(key, None)

    if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired user cache entries")


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


# Multi-Photo Meals Support (Feature: 003-update-logic-for)


async def db_get_meal_with_photos(meal_id: uuid.UUID) -> Any | None:
    """Get meal with associated photos and macronutrients.

    Args:
        meal_id: Meal UUID

    Returns:
        MealWithPhotos object or None if not found
    """
    if sb is None:
        raise RuntimeError("Supabase configuration not available")

    from ..schemas import Macronutrients, MealWithPhotos

    try:
        # Get meal
        meal_res = sb.table("meals").select("*").eq("id", str(meal_id)).execute()
        if not meal_res.data:
            return None

        meal_data = meal_res.data[0]

        # Get associated photos
        photos_res = (
            sb.table("photos")
            .select("id, tigris_key, display_order")
            .eq("meal_id", str(meal_id))
            .order("display_order")
            .execute()
        )

        # Build photo list with presigned URLs
        photos = []
        for photo in photos_res.data if photos_res.data else []:
            try:
                # Generate presigned URLs (1 hour expiry)
                from .storage import generate_presigned_url

                thumbnail_url = generate_presigned_url(photo["tigris_key"], expiry=3600)
                full_url = generate_presigned_url(photo["tigris_key"], expiry=3600)

                photos.append(
                    MealPhotoInfo(
                        id=photo["id"],
                        thumbnailUrl=thumbnail_url,
                        fullUrl=full_url,
                        displayOrder=photo["display_order"],
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to generate photo URLs for meal {meal_id}: {e}")
                # Still add the photo info but with placeholder URLs
                photos.append(
                    MealPhotoInfo(
                        id=photo["id"],
                        thumbnailUrl="",
                        fullUrl="",
                        displayOrder=photo["display_order"],
                    )
                )

        # Build meal object
        macros = Macronutrients(
            protein=meal_data.get("protein_grams", 0) or 0,
            carbs=meal_data.get("carbs_grams", 0) or 0,
            fats=meal_data.get("fats_grams", 0) or 0,
        )

        return MealWithPhotos(
            id=meal_data["id"],
            userId=meal_data["user_id"],
            createdAt=meal_data["created_at"],
            description=meal_data.get("description"),
            calories=meal_data.get("kcal_total", 0),
            macronutrients=macros,
            photos=photos,
            confidenceScore=meal_data.get("confidence_score"),
        )

    except Exception as e:
        logger.error(f"Error getting meal with photos: {e}")
        raise


async def db_get_meals_with_photos(
    user_id: uuid.UUID,
    query_date: Any | None = None,
    start_date: Any | None = None,
    end_date: Any | None = None,
    limit: int = 50,
) -> list[Any]:
    """Get meals with photos for date/range (filters meals older than 1 year).

    Args:
        user_id: User UUID
        query_date: Specific date to query
        start_date: Start of date range
        end_date: End of date range
        limit: Maximum number of meals

    Returns:
        List of MealWithPhotos objects
    """
    if sb is None:
        raise RuntimeError("Supabase configuration not available")

    from datetime import date as date_type

    from ..schemas import Macronutrients, MealWithPhotos

    try:
        # Build query with 1-year retention filter
        one_year_ago = (date_type.today() - timedelta(days=365)).isoformat()

        query = (
            sb.table("meals")
            .select("*")
            .eq("user_id", str(user_id))
            .gte("created_at", one_year_ago)
        )

        # Apply date filters
        if query_date:
            query = query.gte("created_at", f"{query_date}T00:00:00").lt(
                "created_at", f"{query_date}T23:59:59.999999"
            )
        elif start_date and end_date:
            query = query.gte("created_at", f"{start_date}T00:00:00").lte(
                "created_at", f"{end_date}T23:59:59.999999"
            )

        # Order and limit
        query = query.order("created_at", desc=True).limit(limit)

        meals_res = query.execute()

        if not meals_res.data:
            return []

        # Get all meal IDs for batch photo query
        meal_ids = [meal["id"] for meal in meals_res.data]

        # Single query to get all photos for all meals
        photos_res = (
            sb.table("photos")
            .select("id, tigris_key, display_order, meal_id")
            .in_("meal_id", meal_ids)
            .order("display_order")
            .execute()
        )

        # Group photos by meal_id
        photos_by_meal = {}
        for photo in photos_res.data if photos_res.data else []:
            meal_id = photo["meal_id"]
            if meal_id not in photos_by_meal:
                photos_by_meal[meal_id] = []
            photos_by_meal[meal_id].append(photo)

        # Batch fetch all estimates for meals that need descriptions
        estimate_ids = [
            meal["estimate_id"]
            for meal in meals_res.data
            if meal.get("estimate_id") and not meal.get("description")
        ]

        estimates_by_id = {}
        if estimate_ids:
            estimates_res = sb.table("estimates").select("*").in_("id", estimate_ids).execute()
            estimates_by_id = {est["id"]: est for est in estimates_res.data if estimates_res.data}

        # Build result meals
        result_meals = []
        for meal_data in meals_res.data:
            meal_id = meal_data["id"]
            meal_photos = photos_by_meal.get(meal_id, [])

            # Build photo list
            photos = []
            for photo in meal_photos:
                try:
                    from .storage import generate_presigned_url

                    thumbnail_url = generate_presigned_url(photo["tigris_key"], expiry=3600)
                    full_url = generate_presigned_url(photo["tigris_key"], expiry=3600)

                    photos.append(
                        MealPhotoInfo(
                            id=photo["id"],
                            thumbnailUrl=thumbnail_url,
                            fullUrl=full_url,
                            displayOrder=photo["display_order"],
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate photo URLs for meal {meal_id}: {e}")
                    # Still add the photo info but with placeholder URLs
                    photos.append(
                        MealPhotoInfo(
                            id=photo["id"],
                            thumbnailUrl="",
                            fullUrl="",
                            displayOrder=photo["display_order"],
                        )
                    )

            # Build macronutrients
            macros = Macronutrients(
                protein=meal_data.get("protein_grams", 0) or 0,
                carbs=meal_data.get("carbs_grams", 0) or 0,
                fats=meal_data.get("fats_grams", 0) or 0,
            )

            # Generate description from batched estimates
            description = meal_data.get("description")
            if not description and meal_data.get("estimate_id"):
                estimate = estimates_by_id.get(meal_data["estimate_id"])
                if estimate:
                    description = _generate_meal_description(estimate)
                else:
                    description = "No description available"
            elif not description:
                description = "Manual entry"

            result_meals.append(
                MealWithPhotos(
                    id=meal_data["id"],
                    userId=meal_data["user_id"],
                    createdAt=meal_data["created_at"],
                    description=description,
                    calories=meal_data.get("kcal_total", 0),
                    macronutrients=macros,
                    photos=photos,
                    confidenceScore=meal_data.get("confidence_score"),
                )
            )

        return result_meals

    except Exception as e:
        logger.error(f"Error getting meals with photos: {e}")
        raise


async def db_update_meal_with_macros(meal_id: uuid.UUID, updates: Any) -> Any | None:
    """Update meal and recalculate calories from macronutrients.

    Args:
        meal_id: Meal UUID
        updates: MealUpdate object

    Returns:
        Updated MealWithPhotos or None
    """
    if sb is None:
        raise RuntimeError("Supabase configuration not available")

    try:
        # Build update dict
        update_data: dict[str, Any] = {}

        if updates.description is not None:
            update_data["description"] = updates.description

        if updates.protein_grams is not None:
            update_data["protein_grams"] = updates.protein_grams

        if updates.carbs_grams is not None:
            update_data["carbs_grams"] = updates.carbs_grams

        if updates.fats_grams is not None:
            update_data["fats_grams"] = updates.fats_grams

        # Recalculate calories if macros updated (4-4-9 formula)
        if any(k in update_data for k in ["protein_grams", "carbs_grams", "fats_grams"]):
            # Get current meal to fill missing macros
            current_meal_res = sb.table("meals").select("*").eq("id", str(meal_id)).execute()
            if current_meal_res.data:
                current = current_meal_res.data[0]
                protein = update_data.get("protein_grams", current.get("protein_grams", 0) or 0)
                carbs = update_data.get("carbs_grams", current.get("carbs_grams", 0) or 0)
                fats = update_data.get("fats_grams", current.get("fats_grams", 0) or 0)

                # Calculate: 4 kcal/g protein, 4 kcal/g carbs, 9 kcal/g fats
                update_data["kcal_total"] = protein * 4 + carbs * 4 + fats * 9

        # Update meal
        res = sb.table("meals").update(update_data).eq("id", str(meal_id)).execute()

        if not res.data:
            return None

        # Return updated meal with photos
        return await db_get_meal_with_photos(meal_id)

    except Exception as e:
        logger.error(f"Error updating meal with macros: {e}")
        raise


async def db_get_meals_calendar_summary(
    user_id: uuid.UUID, start_date: Any, end_date: Any
) -> list[Any]:
    """Get daily meal summaries for calendar view.

    Args:
        user_id: User UUID
        start_date: Start date
        end_date: End date

    Returns:
        List of MealCalendarDay objects
    """
    if sb is None:
        raise RuntimeError("Supabase configuration not available")

    from ..schemas import MealCalendarDay

    try:
        # Get all meals in range
        one_year_ago = (date.today() - timedelta(days=365)).isoformat()

        meals_res = (
            sb.table("meals")
            .select("created_at, kcal_total, protein_grams, carbs_grams, fats_grams")
            .eq("user_id", str(user_id))
            .gte("created_at", one_year_ago)
            .gte("created_at", f"{start_date}T00:00:00")
            .lte("created_at", f"{end_date}T23:59:59.999999")
            .execute()
        )

        if not meals_res.data:
            return []

        # Aggregate by date
        daily_data: dict[str, dict[str, float]] = {}

        for meal in meals_res.data:
            # Extract date from timestamp
            meal_date = meal["created_at"].split("T")[0]

            if meal_date not in daily_data:
                daily_data[meal_date] = {
                    "count": 0,
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fats": 0,
                }

            daily_data[meal_date]["count"] += 1
            daily_data[meal_date]["calories"] += meal.get("kcal_total", 0) or 0
            daily_data[meal_date]["protein"] += meal.get("protein_grams", 0) or 0
            daily_data[meal_date]["carbs"] += meal.get("carbs_grams", 0) or 0
            daily_data[meal_date]["fats"] += meal.get("fats_grams", 0) or 0

        # Build response
        calendar_days = []
        for date_str, data in sorted(daily_data.items(), reverse=True):
            calendar_days.append(
                MealCalendarDay(
                    meal_date=datetime.fromisoformat(date_str).date(),
                    meal_count=int(data["count"]),
                    total_calories=data["calories"],
                    total_protein=data["protein"],
                    total_carbs=data["carbs"],
                    total_fats=data["fats"],
                )
            )

        return calendar_days

    except Exception as e:
        logger.error(f"Error getting calendar summary: {e}")
        raise
