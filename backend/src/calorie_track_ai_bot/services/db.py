import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from psycopg.types.json import Json

from ..schemas import (
    InlineAnalyticsDaily,
    InlineChatType,
    MealCreateFromEstimateRequest,
    MealCreateManualRequest,
    MealPhotoInfo,
    UIConfiguration,
    UIConfigurationUpdate,
)
from .config import logger
from .database import get_pool
from .storage import BUCKET_NAME, s3

# User ID cache to reduce database queries
_user_id_cache: dict[str, str] = {}
_user_cache_ttl: dict[str, datetime] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


async def db_create_photo(
    tigris_key: str,
    user_id: str | None = None,
    display_order: int = 0,
    media_group_id: str | None = None,
) -> str:
    """Create a photo record in the database."""
    pool = await get_pool()

    logger.debug(
        f"Creating photo record: tigris_key={tigris_key}, user_id={user_id}, "
        f"display_order={display_order}, media_group_id={media_group_id}"
    )
    pid = str(uuid.uuid4())

    async with pool.connection() as conn:
        await conn.execute(
            """INSERT INTO photos (id, tigris_key, user_id, display_order, media_group_id)
               VALUES (%s, %s, %s, %s, %s)""",
            (pid, tigris_key, user_id, display_order, media_group_id),
        )

    logger.info(f"Photo record created with ID: {pid}")
    return pid


async def db_get_or_create_user(
    telegram_id: int, handle: str | None = None, locale: str = "en"
) -> str:
    """Get existing user or create new one based on telegram_id."""
    pool = await get_pool()

    logger.debug(f"Looking up user with telegram_id: {telegram_id}")

    async with pool.connection() as conn:
        row = await conn.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        result = await row.fetchone()
        user = dict(result) if result else None

        if user:
            user_id = str(user["id"])
            logger.info(f"Found existing user with ID: {user_id}")
            return user_id

        # Create new user
        user_id = str(uuid.uuid4())
        logger.info(f"Creating new user with ID: {user_id}, telegram_id: {telegram_id}")
        await conn.execute(
            "INSERT INTO users (id, telegram_id, handle, locale) VALUES (%s, %s, %s, %s)",
            (user_id, telegram_id, handle, locale),
        )
        return user_id


async def db_save_estimate(
    photo_id: str, est: dict[str, Any], photo_ids: list[str] | None = None
) -> str:
    pool = await get_pool()

    eid = str(uuid.uuid4())

    # Build columns and values dynamically
    columns = [
        "id",
        "photo_id",
        "kcal_mean",
        "kcal_min",
        "kcal_max",
        "confidence",
        "items",
        "status",
        "macronutrients",
        "photo_count",
    ]
    values: list[Any] = [
        eid,
        photo_id,
        est.get("kcal_mean"),
        est.get("kcal_min"),
        est.get("kcal_max"),
        est.get("confidence"),
        Json(est["items"]) if est.get("items") is not None else None,
        est.get("status", "done"),
        Json(est["macronutrients"]) if est.get("macronutrients") is not None else None,
        est.get("photo_count"),
    ]

    if photo_ids:
        columns.append("photo_ids")
        values.append(photo_ids)

    placeholders = ", ".join(["%s"] * len(values))
    col_names = ", ".join(columns)

    async with pool.connection() as conn:
        await conn.execute(
            f"INSERT INTO estimates ({col_names}) VALUES ({placeholders})",  # type: ignore[arg-type]
            tuple(values),
        )

    return eid


async def db_get_estimate(estimate_id: str) -> dict[str, Any] | None:
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM estimates WHERE id = %s", (estimate_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_get_photo(photo_id: str) -> dict[str, Any] | None:
    """Get photo record by ID."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM photos WHERE id = %s", (photo_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_get_user(user_id: str) -> dict[str, Any] | None:
    """Get user record by ID."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_create_meal_from_manual(data: MealCreateManualRequest) -> dict[str, str]:
    pool = await get_pool()

    mid = str(uuid.uuid4())
    async with pool.connection() as conn:
        await conn.execute(
            """INSERT INTO meals (id, user_id, meal_date, meal_type, kcal_total, source)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (mid, None, data.meal_date, data.meal_type.value, data.kcal_total, "manual"),
        )
    return {"meal_id": mid}


async def db_create_meal_from_estimate(
    data: MealCreateFromEstimateRequest, user_id: str
) -> dict[str, str]:
    pool = await get_pool()

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
    macronutrients = estimate.get("macronutrients") or {}
    protein_grams = macronutrients.get("protein", 0)
    carbs_grams = macronutrients.get("carbs", 0)
    fats_grams = macronutrients.get("fats", 0)

    # Apply overrides if provided
    if data.overrides and isinstance(data.overrides, dict):
        protein_grams = data.overrides.get("protein_grams", protein_grams)
        carbs_grams = data.overrides.get("carbs_grams", carbs_grams)
        fats_grams = data.overrides.get("fats_grams", fats_grams)

    async with pool.connection() as conn:
        await conn.execute(
            """INSERT INTO meals (id, user_id, meal_date, meal_type, kcal_total,
                                  protein_grams, carbs_grams, fats_grams, source, estimate_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                mid,
                user_id,
                data.meal_date,
                data.meal_type.value,
                kcal_total,
                protein_grams,
                carbs_grams,
                fats_grams,
                "photo",
                data.estimate_id,
            ),
        )

        # Link photos to the meal
        photo_ids = estimate.get("photo_ids") or []
        if not photo_ids:
            single_photo_id = estimate.get("photo_id")
            if single_photo_id:
                photo_ids = [str(single_photo_id)]

        for i, photo_id in enumerate(photo_ids[:5]):
            await conn.execute(
                "UPDATE photos SET meal_id = %s, display_order = %s WHERE id = %s",
                (mid, i, photo_id),
            )

        if photo_ids:
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
        if "macros" not in meal:
            meal["macros"] = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}
        if "description" not in meal:
            meal["description"] = "Manual entry"
        if "corrected" not in meal:
            meal["corrected"] = False
        if "updated_at" not in meal and "created_at" in meal:
            meal["updated_at"] = meal["created_at"]
        elif "updated_at" not in meal:
            now = datetime.now(UTC).isoformat()
            meal["created_at"] = now
            meal["updated_at"] = now
        return

    estimate = await db_get_estimate(str(meal["estimate_id"]))
    if not estimate:
        logger.warning(f"Estimate {meal['estimate_id']} not found for meal {meal['id']}")
        meal["photo_url"] = None
        meal["macros"] = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}
        meal["corrected"] = False
        if "updated_at" not in meal and "created_at" in meal:
            meal["updated_at"] = meal["created_at"]
        elif "updated_at" not in meal:
            now = datetime.now(UTC).isoformat()
            meal["created_at"] = now
            meal["updated_at"] = now
        return

    photo = await db_get_photo(str(estimate["photo_id"]))
    if photo and s3:
        try:
            photo_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": photo["tigris_key"]},
                ExpiresIn=3600,
            )
            meal["photo_url"] = photo_url
        except Exception as e:
            logger.warning(f"Failed to generate photo URL for meal {meal['id']}: {e}")
            meal["photo_url"] = None
    else:
        meal["photo_url"] = None

    meal["macros"] = {
        "protein_g": meal.get("protein_grams", 0) or 0,
        "fat_g": meal.get("fats_grams", 0) or 0,
        "carbs_g": meal.get("carbs_grams", 0) or 0,
    }
    meal["description"] = _generate_meal_description(estimate)
    meal["corrected"] = False

    if "updated_at" not in meal and "created_at" in meal:
        meal["updated_at"] = meal["created_at"]
    elif "updated_at" not in meal:
        now = datetime.now(UTC).isoformat()
        meal["created_at"] = now
        meal["updated_at"] = now


async def resolve_user_id(telegram_user_id: str | None) -> str | None:
    """Resolve Telegram user ID to database UUID with caching."""
    if not telegram_user_id:
        return None

    try:
        _cleanup_user_cache()

        current_time = datetime.now(UTC)
        if telegram_user_id in _user_id_cache:
            if (
                telegram_user_id in _user_cache_ttl
                and _user_cache_ttl[telegram_user_id] > current_time
            ):
                logger.debug(f"User ID cache hit for telegram_id: {telegram_user_id}")
                return _user_id_cache[telegram_user_id]
            else:
                _user_id_cache.pop(telegram_user_id, None)
                _user_cache_ttl.pop(telegram_user_id, None)

        telegram_id_int = int(telegram_user_id)
        user_id = await db_get_or_create_user(telegram_id_int)

        if user_id:
            _user_id_cache[telegram_user_id] = user_id
            _user_cache_ttl[telegram_user_id] = current_time + timedelta(seconds=CACHE_TTL_SECONDS)
            logger.debug(f"User ID cached for telegram_id: {telegram_user_id}")

        return user_id
    except (ValueError, TypeError):
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
    pool = await get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                "SELECT * FROM meals WHERE meal_date = %s AND user_id = %s",
                (meal_date, user_id),
            )
        else:
            cur = await conn.execute("SELECT * FROM meals WHERE meal_date = %s", (meal_date,))
        rows = await cur.fetchall()
        meals = [dict(r) for r in rows]

    for meal in meals:
        await _enhance_meal_with_related_data(meal)

    return meals


async def db_get_meal(meal_id: str) -> dict[str, Any] | None:
    """Get a specific meal by ID with related data."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM meals WHERE id = %s", (meal_id,))
        row = await cur.fetchone()

    if not row:
        return None

    meal = dict(row)
    await _enhance_meal_with_related_data(meal)
    return meal


async def db_update_meal(meal_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    """Update a meal with the given updates."""
    pool = await get_pool()

    if not updates:
        return None

    set_clauses = []
    values: list[Any] = []
    for key, val in updates.items():
        set_clauses.append(f"{key} = %s")
        values.append(val)
    values.append(meal_id)

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"UPDATE meals SET {', '.join(set_clauses)} WHERE id = %s RETURNING *",
            tuple(values),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_delete_meal(meal_id: str) -> bool:
    """Delete a meal by ID."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("DELETE FROM meals WHERE id = %s RETURNING id", (meal_id,))
        row = await cur.fetchone()
        return row is not None


async def db_get_daily_summary(
    date: str, telegram_user_id: str | None = None
) -> dict[str, Any] | None:
    """Get daily summary for a specific date."""
    pool = await get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                "SELECT kcal_total FROM meals WHERE meal_date = %s AND user_id = %s",
                (date, user_id),
            )
        else:
            cur = await conn.execute("SELECT kcal_total FROM meals WHERE meal_date = %s", (date,))
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    total_kcal = sum(meal.get("kcal_total", 0) for meal in meals)
    macro_totals = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

    return {
        "user_id": user_id,
        "date": date,
        "kcal_total": total_kcal,
        "macros_totals": macro_totals,
    }


async def db_get_goal(telegram_user_id: str) -> dict[str, Any] | None:
    """Get user's goal."""
    pool = await get_pool()

    user_id = await resolve_user_id(telegram_user_id)
    if not user_id:
        return None

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM goals WHERE user_id = %s", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_create_or_update_goal(telegram_user_id: str, daily_kcal_target: int) -> dict[str, Any]:
    """Create or update user's goal."""
    pool = await get_pool()

    user_id = await resolve_user_id(telegram_user_id)
    if not user_id:
        raise ValueError(f"Could not resolve user ID for telegram_user_id: {telegram_user_id}")

    existing = await db_get_goal(telegram_user_id)

    async with pool.connection() as conn:
        if existing:
            cur = await conn.execute(
                "UPDATE goals SET daily_kcal_target = %s, updated_at = NOW() WHERE id = %s RETURNING *",
                (daily_kcal_target, existing["id"]),
            )
            row = await cur.fetchone()
            if row:
                return dict(row)

        # Create new goal
        goal_id = str(uuid.uuid4())
        await conn.execute(
            "INSERT INTO goals (id, user_id, daily_kcal_target) VALUES (%s, %s, %s)",
            (goal_id, user_id, daily_kcal_target),
        )
        return {"id": goal_id, "user_id": user_id, "daily_kcal_target": daily_kcal_target}


async def db_get_summaries_by_date_range(
    start_date: str, end_date: str, telegram_user_id: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get summaries for a date range in a single query."""
    pool = await get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                """SELECT meal_date, kcal_total FROM meals
                   WHERE meal_date >= %s AND meal_date <= %s AND user_id = %s""",
                (start_date, end_date, user_id),
            )
        else:
            cur = await conn.execute(
                "SELECT meal_date, kcal_total FROM meals WHERE meal_date >= %s AND meal_date <= %s",
                (start_date, end_date),
            )
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    summaries: dict[str, dict[str, Any]] = {}
    for meal in meals:
        d = str(meal["meal_date"])
        if d not in summaries:
            summaries[d] = {
                "user_id": user_id,
                "date": d,
                "kcal_total": 0,
                "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
            }
        summaries[d]["kcal_total"] += meal.get("kcal_total", 0)

    return summaries


async def db_get_today_data(date: str, telegram_user_id: str | None = None) -> dict[str, Any]:
    """Get all data needed for the Today page in a single query."""
    pool = await get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                "SELECT * FROM meals WHERE meal_date = %s AND user_id = %s",
                (date, user_id),
            )
        else:
            cur = await conn.execute("SELECT * FROM meals WHERE meal_date = %s", (date,))
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    daily_summary = {
        "user_id": user_id,
        "date": date,
        "kcal_total": sum(meal.get("kcal_total", 0) for meal in meals),
        "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
    }

    return {"meals": meals, "daily_summary": daily_summary}


# UI Configuration Database Functions
async def db_get_ui_configuration(user_id: str) -> dict[str, Any] | None:
    """Get UI configuration for a user."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM ui_configurations WHERE user_id = %s", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_create_ui_configuration(user_id: str, config: UIConfiguration) -> dict[str, Any]:
    """Create a new UI configuration for a user."""
    pool = await get_pool()

    config_data = {
        "id": str(config.id),
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
        "features": Json(config.features) if config.features is not None else None,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }

    columns = ", ".join(config_data.keys())
    placeholders = ", ".join(["%s"] * len(config_data))

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"INSERT INTO ui_configurations ({columns}) VALUES ({placeholders}) RETURNING *",  # type: ignore[arg-type]
            tuple(config_data.values()),
        )
        row = await cur.fetchone()
        return dict(row) if row else config_data


async def db_update_ui_configuration(
    user_id: str, config_id: str, updates: UIConfigurationUpdate
) -> dict[str, Any] | None:
    """Update an existing UI configuration."""
    pool = await get_pool()

    update_data: dict[str, Any] = {}
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
        update_data["features"] = Json(updates.features)

    update_data["updated_at"] = datetime.now(UTC).isoformat()

    set_clauses = [f"{k} = %s" for k in update_data]
    values = [*list(update_data.values()), config_id, user_id]

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"UPDATE ui_configurations SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s RETURNING *",  # type: ignore[arg-type]
            tuple(values),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_delete_ui_configuration(user_id: str, config_id: str) -> bool:
    """Delete a UI configuration."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute(
            "DELETE FROM ui_configurations WHERE id = %s AND user_id = %s RETURNING id",
            (config_id, user_id),
        )
        row = await cur.fetchone()
        return row is not None


async def db_get_ui_configurations_by_user(user_id: str) -> list[dict[str, Any]]:
    """Get all UI configurations for a user."""
    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT * FROM ui_configurations WHERE user_id = %s ORDER BY updated_at DESC",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def db_cleanup_old_ui_configurations(user_id: str, keep_count: int = 5) -> int:
    """Clean up old UI configurations, keeping only the most recent ones."""
    all_configs = await db_get_ui_configurations_by_user(user_id)

    if len(all_configs) <= keep_count:
        return 0

    configs_to_delete = all_configs[keep_count:]
    delete_ids = [config["id"] for config in configs_to_delete]

    if not delete_ids:
        return 0

    pool = await get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute(
            "DELETE FROM ui_configurations WHERE id = ANY(%s) AND user_id = %s RETURNING id",
            (delete_ids, user_id),
        )
        rows = await cur.fetchall()
        deleted_count = len(rows)

    logger.info(f"Cleaned up {deleted_count} old UI configurations for user {user_id}")
    return deleted_count


# Multi-Photo Meals Support


async def db_get_meal_with_photos(meal_id: uuid.UUID) -> Any | None:
    """Get meal with associated photos and macronutrients."""
    pool = await get_pool()

    from ..schemas import Macronutrients, MealWithPhotos

    try:
        async with pool.connection() as conn:
            cur = await conn.execute("SELECT * FROM meals WHERE id = %s", (str(meal_id),))
            meal_data = await cur.fetchone()
            if not meal_data:
                return None
            meal_data = dict(meal_data)

            cur = await conn.execute(
                """SELECT id, tigris_key, display_order FROM photos
                   WHERE meal_id = %s ORDER BY display_order""",
                (str(meal_id),),
            )
            photo_rows: list[dict[str, Any]] = [dict(r) for r in await cur.fetchall()]

        photos = []
        for photo in photo_rows:
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
                photos.append(
                    MealPhotoInfo(
                        id=photo["id"],
                        thumbnailUrl="",
                        fullUrl="",
                        displayOrder=photo["display_order"],
                    )
                )

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
    """Get meals with photos for date/range (filters meals older than 1 year)."""
    pool = await get_pool()

    from datetime import date as date_type

    from ..schemas import Macronutrients, MealWithPhotos

    try:
        one_year_ago = (date_type.today() - timedelta(days=365)).isoformat()

        # Build query
        conditions = ["user_id = %s", "created_at >= %s"]
        params: list[Any] = [str(user_id), one_year_ago]

        if query_date:
            conditions.append("created_at >= %s")
            conditions.append("created_at < %s")
            params.append(f"{query_date}T00:00:00")
            params.append(f"{query_date}T23:59:59.999999")
        elif start_date and end_date:
            conditions.append("created_at >= %s")
            conditions.append("created_at <= %s")
            params.append(f"{start_date}T00:00:00")
            params.append(f"{end_date}T23:59:59.999999")

        where = " AND ".join(conditions)
        params.append(limit)

        async with pool.connection() as conn:
            cur = await conn.execute(
                f"SELECT * FROM meals WHERE {where} ORDER BY created_at DESC LIMIT %s",  # type: ignore[arg-type]
                tuple(params),
            )
            meals_data: list[dict[str, Any]] = [dict(r) for r in await cur.fetchall()]

            if not meals_data:
                return []

            meal_ids = [str(m["id"]) for m in meals_data]

            cur = await conn.execute(
                """SELECT id, tigris_key, display_order, meal_id FROM photos
                   WHERE meal_id = ANY(%s) ORDER BY display_order""",
                (meal_ids,),
            )
            photos_data: list[dict[str, Any]] = [dict(r) for r in await cur.fetchall()]

            # Batch fetch estimates
            estimate_ids = [
                str(m["estimate_id"])
                for m in meals_data
                if m.get("estimate_id") and not m.get("description")
            ]

            estimates_by_id: dict[str, dict[str, Any]] = {}
            if estimate_ids:
                cur = await conn.execute(
                    "SELECT * FROM estimates WHERE id = ANY(%s)", (estimate_ids,)
                )
                estimates_by_id = {str(e["id"]): e for e in (dict(r) for r in await cur.fetchall())}

        # Group photos by meal_id
        photos_by_meal: dict[str, list[dict[str, Any]]] = {}
        for photo in photos_data:
            mid = str(photo["meal_id"])
            if mid not in photos_by_meal:
                photos_by_meal[mid] = []
            photos_by_meal[mid].append(photo)

        result_meals = []
        for meal_data in meals_data:
            meal_id = str(meal_data["id"])
            meal_photos = photos_by_meal.get(meal_id, [])

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
                    photos.append(
                        MealPhotoInfo(
                            id=photo["id"],
                            thumbnailUrl="",
                            fullUrl="",
                            displayOrder=photo["display_order"],
                        )
                    )

            macros = Macronutrients(
                protein=meal_data.get("protein_grams", 0) or 0,
                carbs=meal_data.get("carbs_grams", 0) or 0,
                fats=meal_data.get("fats_grams", 0) or 0,
            )

            description = meal_data.get("description")
            if not description and meal_data.get("estimate_id"):
                estimate = estimates_by_id.get(str(meal_data["estimate_id"]))
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
    """Update meal and recalculate calories from macronutrients."""
    pool = await get_pool()

    try:
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
            async with pool.connection() as conn:
                cur = await conn.execute("SELECT * FROM meals WHERE id = %s", (str(meal_id),))
                current = await cur.fetchone()

            if current:
                current = dict(current)
                protein = update_data.get("protein_grams", current.get("protein_grams", 0) or 0)
                carbs = update_data.get("carbs_grams", current.get("carbs_grams", 0) or 0)
                fats = update_data.get("fats_grams", current.get("fats_grams", 0) or 0)
                update_data["kcal_total"] = protein * 4 + carbs * 4 + fats * 9

        if not update_data:
            return None

        set_clauses = [f"{k} = %s" for k in update_data]
        values = [*list(update_data.values()), str(meal_id)]

        async with pool.connection() as conn:
            await conn.execute(
                f"UPDATE meals SET {', '.join(set_clauses)} WHERE id = %s",  # type: ignore[arg-type]
                tuple(values),
            )

        return await db_get_meal_with_photos(meal_id)

    except Exception as e:
        logger.error(f"Error updating meal with macros: {e}")
        raise


async def db_get_meals_calendar_summary(
    user_id: uuid.UUID, start_date: Any, end_date: Any
) -> list[Any]:
    """Get daily meal summaries for calendar view."""
    pool = await get_pool()

    from ..schemas import MealCalendarDay

    try:
        one_year_ago = (date.today() - timedelta(days=365)).isoformat()

        async with pool.connection() as conn:
            cur = await conn.execute(
                """SELECT created_at, kcal_total, protein_grams, carbs_grams, fats_grams
                   FROM meals
                   WHERE user_id = %s AND created_at >= %s
                     AND created_at >= %s AND created_at <= %s""",
                (
                    str(user_id),
                    one_year_ago,
                    f"{start_date}T00:00:00",
                    f"{end_date}T23:59:59.999999",
                ),
            )
            rows = await cur.fetchall()

        if not rows:
            return []

        daily_data: dict[str, dict[str, float]] = {}
        for meal in rows:
            meal = dict(meal)
            meal_date = str(meal["created_at"]).split("T")[0]

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


# Inline analytics helpers


def _inline_defaults(date_value: date, chat_type: InlineChatType) -> InlineAnalyticsDaily:
    return InlineAnalyticsDaily(
        id=uuid.uuid4(),
        date=date_value,
        chat_type=chat_type,
        trigger_counts={},
        request_count=0,
        success_count=0,
        failure_count=0,
        permission_block_count=0,
        avg_ack_latency_ms=0,
        p95_result_latency_ms=0,
        accuracy_within_tolerance_pct=0.0,
        failure_reasons=[],
        last_updated_at=datetime.now(UTC),
    )


def _to_inline_daily_model(row: dict[str, Any]) -> InlineAnalyticsDaily:
    payload = {**row}
    payload.setdefault("trigger_counts", {})
    payload.setdefault("failure_reasons", [])
    payload.setdefault("permission_block_count", 0)
    payload.setdefault("request_count", 0)
    payload.setdefault("success_count", 0)
    payload.setdefault("failure_count", 0)
    payload.setdefault("avg_ack_latency_ms", 0)
    payload.setdefault("p95_result_latency_ms", 0)
    payload.setdefault("accuracy_within_tolerance_pct", 0.0)
    payload.setdefault("last_updated_at", datetime.now(UTC).isoformat())
    return InlineAnalyticsDaily(**payload)


def _inline_payload(daily: InlineAnalyticsDaily) -> dict[str, Any]:
    payload = daily.model_dump(mode="json")
    if payload.get("failure_reasons") is None:
        payload["failure_reasons"] = []
    if payload.get("trigger_counts") is None:
        payload["trigger_counts"] = {}
    return payload


async def db_upsert_inline_analytics(daily: InlineAnalyticsDaily) -> InlineAnalyticsDaily:
    pool = await get_pool()

    payload = _inline_payload(daily)

    # Wrap jsonb columns with Json()
    jsonb_keys = {"trigger_counts", "failure_reasons"}
    adapted_values = [
        Json(v) if k in jsonb_keys and v is not None else v for k, v in payload.items()
    ]

    columns = ", ".join(payload.keys())
    placeholders = ", ".join(["%s"] * len(payload))
    update_set = ", ".join(f"{k} = EXCLUDED.{k}" for k in payload if k not in ("id",))

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"""INSERT INTO inline_analytics_daily ({columns}) VALUES ({placeholders})
                ON CONFLICT (date, chat_type) DO UPDATE SET {update_set}
                RETURNING *""",  # type: ignore[arg-type]
            tuple(adapted_values),
        )
        row = await cur.fetchone()

    returned = dict(row) if row else payload
    return _to_inline_daily_model(returned)


async def db_fetch_inline_analytics(
    range_start: date, range_end: date, chat_type: str | None = None
) -> list[InlineAnalyticsDaily]:
    pool = await get_pool()

    async with pool.connection() as conn:
        if chat_type:
            cur = await conn.execute(
                """SELECT * FROM inline_analytics_daily
                   WHERE date >= %s AND date <= %s AND chat_type = %s
                   ORDER BY date""",
                (range_start, range_end, chat_type),
            )
        else:
            cur = await conn.execute(
                """SELECT * FROM inline_analytics_daily
                   WHERE date >= %s AND date <= %s
                   ORDER BY date""",
                (range_start, range_end),
            )
        rows = await cur.fetchall()

    return [_to_inline_daily_model(dict(row)) for row in rows]


async def db_increment_inline_permission_block(
    *, date_value: date, chat_type: InlineChatType, increment: int = 1
) -> InlineAnalyticsDaily:
    existing_rows = await db_fetch_inline_analytics(date_value, date_value, chat_type.value)
    if existing_rows:
        current = existing_rows[0]
    else:
        current = _inline_defaults(date_value, chat_type)

    updated = current.model_copy(
        update={
            "permission_block_count": current.permission_block_count + increment,
            "last_updated_at": datetime.now(UTC),
        }
    )

    return await db_upsert_inline_analytics(updated)
