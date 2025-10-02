import json
from typing import Any

import redis.asyncio as redis

from .config import APP_ENV, REDIS_URL

# Initialize Redis client only if configuration is available
r: redis.Redis | None = None
QUEUE = "estimate_jobs"

if REDIS_URL is not None:
    r = redis.from_url(REDIS_URL, decode_responses=True)
elif APP_ENV == "dev":
    # In development mode, allow missing Redis config
    print("WARNING: Redis configuration not set. Queue functionality will be disabled.")
    print("To enable queue operations, set the following environment variable:")
    print("- REDIS_URL")
else:
    raise ValueError("REDIS_URL must be set")


async def enqueue_estimate_job(photo_ids: str | list[str], description: str | None = None) -> str:
    """Enqueue an estimation job for one or more photos.

    Args:
        photo_ids: Single photo ID or list of photo IDs
        description: Optional user-provided meal description

    Returns:
        Job ID (first photo ID if single, or joined IDs if multiple)
    """
    if r is None:
        raise RuntimeError("Redis configuration not available. Queue functionality is disabled.")

    # Normalize to list
    if isinstance(photo_ids, str):
        photo_ids = [photo_ids]

    job = {"photo_ids": photo_ids, "description": description}
    await r.lpush(QUEUE, json.dumps(job))  # type: ignore

    # Return first photo ID as job identifier
    return photo_ids[0]


async def dequeue_estimate_job() -> dict[str, Any] | None:
    if r is None:
        raise RuntimeError("Redis configuration not available. Queue functionality is disabled.")

    res = await r.brpop([QUEUE], timeout=10)  # type: ignore
    if res:
        _key, data = res
        return json.loads(data)
    return None
