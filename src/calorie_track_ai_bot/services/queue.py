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


async def enqueue_estimate_job(photo_id: str) -> str:
    if r is None:
        raise RuntimeError("Redis configuration not available. Queue functionality is disabled.")

    job = {"photo_id": photo_id}
    await r.lpush(QUEUE, json.dumps(job))  # type: ignore
    return photo_id


async def dequeue_estimate_job() -> dict[str, Any] | None:
    if r is None:
        raise RuntimeError("Redis configuration not available. Queue functionality is disabled.")

    res = await r.brpop([QUEUE], timeout=10)  # type: ignore
    if res:
        _key, data = res
        return json.loads(data)
    return None
