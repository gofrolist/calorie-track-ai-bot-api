import asyncio
from typing import Any

from ..services.config import logger
from ..services.db import db_get_photo, db_get_user, db_save_estimate
from ..services.estimator import estimate_from_image_url
from ..services.queue import dequeue_estimate_job
from ..services.storage import BUCKET_NAME, s3
from ..services.telegram import get_bot


async def handle_job(job: dict[str, Any]) -> None:
    photo_id = job["photo_id"]
    logger.info(f"Processing estimation job for photo_id: {photo_id}")

    try:
        # Get photo record to retrieve the storage key
        photo_record = await db_get_photo(photo_id)
        if not photo_record:
            raise ValueError(f"Photo record not found for photo_id: {photo_id}")

        tigris_key = photo_record["tigris_key"]
        logger.debug(f"Retrieved tigris_key for photo {photo_id}: {tigris_key}")

        # Generate presigned URL using the actual storage key
        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": tigris_key}, ExpiresIn=900
        )
        logger.debug(f"Generated presigned URL for photo: {photo_id}")

        est = await estimate_from_image_url(url)
        est.setdefault("confidence", 0.5)
        logger.info(f"Estimation completed for photo {photo_id}: {est}")

        estimate_id = await db_save_estimate(photo_id=photo_id, est=est)
        logger.info(f"Estimate saved with ID: {estimate_id} for photo: {photo_id}")

        # Send estimate results back to user via Telegram
        await send_estimate_to_user(photo_record, est, estimate_id)

    except Exception as e:
        logger.error(f"Error processing job for photo {photo_id}: {e}", exc_info=True)
        raise


async def send_estimate_to_user(
    photo_record: dict[str, Any], est: dict[str, Any], estimate_id: str
) -> None:
    """Send calorie estimate results back to user via Telegram."""
    try:
        # Get user information
        user_id = photo_record.get("user_id")
        if not user_id:
            logger.warning("No user_id found in photo record, cannot send estimate")
            return

        user_record = await db_get_user(user_id)
        if not user_record:
            logger.warning(f"User record not found for user_id: {user_id}")
            return

        telegram_id = user_record.get("telegram_id")
        if not telegram_id:
            logger.warning(f"No telegram_id found for user: {user_id}")
            return

        # Format the estimate message
        kcal_mean = est.get("kcal_mean", 0)
        kcal_min = est.get("kcal_min", 0)
        kcal_max = est.get("kcal_max", 0)
        confidence = est.get("confidence", 0)
        items = est.get("items", [])

        # Create message
        message = "🍎 <b>Calorie Estimate Complete!</b>\n\n"
        message += f"📊 <b>Total Calories:</b> {kcal_mean:.0f} kcal\n"
        message += f"📈 <b>Range:</b> {kcal_min:.0f} - {kcal_max:.0f} kcal\n"
        message += f"🎯 <b>Confidence:</b> {confidence:.0%}\n\n"

        if items:
            message += "<b>📋 Food Items:</b>\n"
            for item in items:
                label = item.get("label", "Unknown")
                kcal = item.get("kcal", 0)
                item_confidence = item.get("confidence", 0)
                message += f"• {label}: {kcal:.0f} kcal ({item_confidence:.0%})\n"

        message += f"\n💡 <i>Estimate ID: {estimate_id[:8]}...</i>"

        # Send message via Telegram
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=message, parse_mode="HTML")
        logger.info(f"Estimate sent to user {telegram_id} for photo {photo_record['id']}")

    except Exception as e:
        logger.error(f"Error sending estimate to user: {e}", exc_info=True)


async def main() -> None:
    logger.info("Starting estimation worker")
    while True:
        try:
            job = await dequeue_estimate_job()
            if job:
                logger.debug(f"Dequeued job: {job}")
                await handle_job(job)
            else:
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
            await asyncio.sleep(5)  # Wait before retrying


if __name__ == "__main__":
    asyncio.run(main())
