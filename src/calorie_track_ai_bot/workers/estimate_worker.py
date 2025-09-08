import asyncio
from typing import Any

from ..services.db import db_save_estimate
from ..services.estimator import estimate_from_image_url
from ..services.queue import dequeue_estimate_job
from ..services.storage import BUCKET_NAME, s3


async def handle_job(job: dict[str, Any]) -> None:
    key = job["photo_id"]
    url = s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET_NAME, "Key": key}, ExpiresIn=900
    )
    est = await estimate_from_image_url(url)
    est.setdefault("confidence", 0.5)
    await db_save_estimate(photo_id=key, est=est)


async def main() -> None:
    while True:
        job = await dequeue_estimate_job()
        if job:
            try:
                await handle_job(job)
            except Exception as e:
                print("job error", e)
        else:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
