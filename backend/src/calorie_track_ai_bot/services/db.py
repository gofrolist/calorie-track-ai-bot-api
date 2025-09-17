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
        "macros": data.macros,
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
        "overrides": data.overrides,
        "source": "photo",
        "estimate_id": data.estimate_id,
    }
    sb.table("meals").insert(payload).execute()
    return {"meal_id": mid}
