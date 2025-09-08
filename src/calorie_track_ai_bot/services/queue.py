import json
from typing import Any

import redis.asyncio as redis

from .config import REDIS_URL

if REDIS_URL is None:
    raise ValueError("REDIS_URL must be set")

r = redis.from_url(REDIS_URL, decode_responses=True)
QUEUE = "estimate_jobs"


async def enqueue_estimate_job(photo_id: str) -> str:
    job = {"photo_id": photo_id}
    await r.lpush(QUEUE, json.dumps(job))  # type: ignore
    return photo_id


async def dequeue_estimate_job() -> dict[str, Any] | None:
    res = await r.brpop([QUEUE], timeout=10)  # type: ignore
    if res:
        _key, data = res
        return json.loads(data)
    return None
