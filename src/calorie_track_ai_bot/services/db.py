import uuid
from typing import Any

import httpx
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

from ..schemas import MealCreateFromEstimateRequest, MealCreateManualRequest
from .config import APP_ENV, SUPABASE_KEY, SUPABASE_URL

# Initialize Supabase client only if configuration is available
sb: Any | None = None

if SUPABASE_URL is not None and SUPABASE_KEY is not None:
    # Create a custom httpx client to avoid deprecation warnings
    httpx_client = httpx.Client(timeout=httpx.Timeout(120.0))

    # Create Supabase client with custom options
    options = SyncClientOptions(httpx_client=httpx_client)
    sb = create_client(SUPABASE_URL, SUPABASE_KEY, options)
elif APP_ENV == "dev":
    # In development mode, allow missing Supabase config
    print("WARNING: Supabase configuration not set. Database functionality will be disabled.")
    print("To enable database operations, set the following environment variables:")
    print("- SUPABASE_URL")
    print("- SUPABASE_KEY")
else:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")


async def db_create_photo(tigris_key: str) -> str:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    pid = str(uuid.uuid4())
    sb.table("photos").insert({"id": pid, "tigris_key": tigris_key}).execute()
    return pid


async def db_save_estimate(photo_id: str, est: dict[str, Any]) -> str:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    eid = str(uuid.uuid4())
    sb.table("estimates").insert({"id": eid, "photo_id": photo_id, **est}).execute()
    return eid


async def db_get_estimate(estimate_id: str) -> dict[str, Any] | None:
    if sb is None:
        raise RuntimeError(
            "Supabase configuration not available. Database functionality is disabled."
        )

    res = sb.table("estimates").select("*").eq("id", estimate_id).execute()
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
