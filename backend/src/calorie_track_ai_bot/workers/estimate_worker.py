import asyncio
from datetime import date
from typing import Any

from ..schemas import MealCreateFromEstimateRequest, MealType
from ..services.config import logger
from ..services.db import db_create_meal_from_estimate, db_get_photo, db_get_user, db_save_estimate
from ..services.estimator import CalorieEstimator, estimate_from_image_url
from ..services.queue import dequeue_estimate_job
from ..services.storage import BUCKET_NAME, generate_presigned_url, s3
from ..services.telegram import get_bot


async def handle_job(job: dict[str, Any]) -> None:
    """Handle estimation job for single or multiple photos.

    Feature: 003-update-logic-for (Multi-photo support)
    Supports both legacy single-photo jobs and new multi-photo jobs.
    """
    # Check if this is a multi-photo job
    photo_ids = job.get("photo_ids")  # New multi-photo format
    photo_id = job.get("photo_id")  # Legacy single-photo format
    description = job.get("description")  # Optional user description
    media_group_id = job.get("media_group_id")  # Telegram media group

    if photo_ids:
        # Multi-photo job
        logger.info(f"Processing multi-photo estimation job: {len(photo_ids)} photos")
        await handle_multiphotos_job(photo_ids, description, media_group_id)
    elif photo_id:
        # Legacy single-photo job
        logger.info(f"Processing single-photo estimation job for photo_id: {photo_id}")
        await handle_single_photo_job(photo_id)
    else:
        raise ValueError("Job must contain either photo_id or photo_ids")


async def handle_single_photo_job(photo_id: str) -> None:
    """Handle legacy single-photo estimation job."""
    if photo_id is None:
        raise ValueError("photo_id cannot be None")

    try:
        # Get photo record to retrieve the storage key
        photo_record = await db_get_photo(photo_id)
        if not photo_record:
            raise ValueError(f"Photo record not found for photo_id: {photo_id}")

        tigris_key = photo_record["tigris_key"]
        logger.debug(f"Retrieved tigris_key for photo {photo_id}: {tigris_key}")

        # Generate presigned URL using the actual storage key
        if s3 is None:
            raise RuntimeError("S3 client not available. Tigris configuration is missing.")

        url = s3.generate_presigned_url(
            "get_object", Params={"Bucket": BUCKET_NAME, "Key": tigris_key}, ExpiresIn=900
        )
        logger.debug(f"Generated presigned URL for photo: {photo_id}")

        est = await estimate_from_image_url(url)
        est.setdefault("confidence", 0.5)
        logger.info(f"Estimation completed for photo {photo_id}: {est}")

        estimate_id = await db_save_estimate(photo_id=photo_id, est=est)
        logger.info(f"Estimate saved with ID: {estimate_id} for photo: {photo_id}")

        # Create meal record from estimate
        await create_meal_from_estimate(photo_record, estimate_id)

        # Send estimate results back to user via Telegram
        await send_estimate_to_user(photo_record, est, estimate_id)

    except Exception as e:
        logger.error(f"Error processing job for photo {photo_id}: {e}", exc_info=True)
        raise


async def handle_multiphotos_job(
    photo_ids: list[str], description: str | None = None, media_group_id: str | None = None
) -> None:
    """Handle multi-photo estimation job (Feature: 003-update-logic-for).

    Args:
        photo_ids: List of photo IDs (1-5 photos)
        description: Optional meal description
        media_group_id: Telegram media group identifier
    """
    try:
        logger.info(f"Processing {len(photo_ids)} photos together")

        # Get all photo records and generate presigned URLs
        photo_urls = []
        photo_records = []

        for photo_id in photo_ids:
            photo_record = await db_get_photo(photo_id)
            if not photo_record:
                logger.warning(f"Photo {photo_id} not found, skipping")
                continue

            photo_records.append(photo_record)

            # Generate presigned URL
            tigris_key = photo_record["tigris_key"]
            url = generate_presigned_url(tigris_key, expiry=900)
            photo_urls.append(url)

        if not photo_urls:
            raise ValueError("No valid photos found")

        # Use CalorieEstimator for combined multi-photo analysis
        estimator = CalorieEstimator()
        result = await estimator.estimate_from_photos(
            photo_urls=photo_urls, description=description
        )

        # Save estimate with macronutrients and photo_count
        estimate_data = {
            "kcal_mean": result["calories"]["estimate"],
            "kcal_min": result["calories"]["min"],
            "kcal_max": result["calories"]["max"],
            "confidence": result["confidence"],
            "macronutrients": result["macronutrients"],
            "photo_count": result["photo_count"],
            "items": [],  # Items not provided in multi-photo response yet
        }

        # Save estimate (use first photo as primary)
        estimate_id = await db_save_estimate(photo_id=photo_ids[0], est=estimate_data)
        logger.info(f"Multi-photo estimate saved with ID: {estimate_id}")

        # Create meal from estimate
        if photo_records:
            await create_meal_from_estimate(photo_records[0], estimate_id)

        # Send results to user with macronutrients
        await send_multiphotos_estimate_to_user(
            photo_records[0], result, estimate_id, len(photo_urls)
        )

    except Exception as e:
        logger.error(f"Error processing multi-photo job: {e}", exc_info=True)
        raise


async def create_meal_from_estimate(photo_record: dict[str, Any], estimate_id: str) -> None:
    """Create a meal record from the completed estimate."""
    try:
        user_id = photo_record.get("user_id")
        if not user_id:
            logger.warning("No user_id found in photo record, cannot create meal")
            return

        # Create meal from estimate with default values
        meal_request = MealCreateFromEstimateRequest(
            estimate_id=estimate_id,
            meal_date=date.today(),
            meal_type=MealType.snack,  # Default to snack, user can change in UI
        )

        meal_id = await db_create_meal_from_estimate(meal_request, user_id)
        logger.info(f"Meal created with ID: {meal_id} from estimate: {estimate_id}")

    except Exception as e:
        logger.error(f"Error creating meal from estimate {estimate_id}: {e}", exc_info=True)
        # Don't raise - meal creation failure shouldn't break the estimate workflow


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
        message = "🍎 <b>Nutrition Estimate Complete!</b>\n\n"
        message += f"📊 <b>Total Calories:</b> {kcal_mean:.0f} kcal\n"
        message += f"📈 <b>Range:</b> {kcal_min:.0f} - {kcal_max:.0f} kcal\n"
        message += f"🎯 <b>Confidence:</b> {confidence:.0%}\n\n"

        # Add macronutrients section (placeholder data for now)
        message += "<b>🏋️ Macronutrients:</b>\n"
        message += f"• Protein: ~{kcal_mean * 0.15:.1f}g\n"  # ~15% protein
        message += f"• Fat: ~{kcal_mean * 0.25 / 9:.1f}g\n"  # ~25% fat (~9 cal/g)
        message += f"• Carbs: ~{kcal_mean * 0.6 / 4:.1f}g\n\n"  # ~60% carbs (~4 cal/g)

        if items:
            message += "<b>📋 Food Items:</b>\n"
            for item in items:
                label = item.get("label", "Unknown")
                kcal = item.get("kcal", 0)
                item_confidence = item.get("confidence", 0)
                message += f"• {label}: {kcal:.0f} kcal ({item_confidence:.0%})\n"

        # Send message via Telegram
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=message, parse_mode="HTML")
        logger.info(f"Estimate sent to user {telegram_id} for photo {photo_record['id']}")

    except Exception as e:
        logger.error(f"Error sending estimate to user: {e}", exc_info=True)


async def send_multiphotos_estimate_to_user(
    photo_record: dict[str, Any], result: dict[str, Any], estimate_id: str, photo_count: int
) -> None:
    """Send multi-photo estimate results with actual macronutrients (Feature: 003-update-logic-for)."""
    try:
        # Get user information
        user_id = photo_record.get("user_id")
        if not user_id:
            logger.warning("No user_id found, cannot send estimate")
            return

        user_record = await db_get_user(user_id)
        if not user_record:
            logger.warning(f"User record not found for user_id: {user_id}")
            return

        telegram_id = user_record.get("telegram_id")
        if not telegram_id:
            logger.warning(f"No telegram_id found for user: {user_id}")
            return

        # Extract data from result
        calories = result["calories"]["estimate"]
        kcal_min = result["calories"]["min"]
        kcal_max = result["calories"]["max"]
        confidence = result["confidence"]
        macros = result["macronutrients"]

        # Create enhanced message with actual macronutrients
        message = "🍎 <b>Nutrition Estimate Complete!</b>\n"
        message += f"📸 <i>Analyzed {photo_count} photo(s)</i>\n\n"
        message += f"📊 <b>Total Calories:</b> {calories:.0f} kcal\n"
        message += f"📈 <b>Range:</b> {kcal_min:.0f} - {kcal_max:.0f} kcal\n"
        message += f"🎯 <b>Confidence:</b> {confidence:.0%}\n\n"

        # Add actual macronutrients from AI
        message += "<b>🏋️ Macronutrients:</b>\n"
        message += f"• Protein: {macros['protein']:.1f}g\n"
        message += f"• Carbs: {macros['carbs']:.1f}g\n"
        message += f"• Fats: {macros['fats']:.1f}g\n"

        # Send message
        bot = get_bot()
        await bot.send_message(chat_id=telegram_id, text=message, parse_mode="HTML")
        logger.info(
            f"Multi-photo estimate sent to user {telegram_id}: "
            f"{photo_count} photos, {calories:.0f} kcal"
        )

    except Exception as e:
        logger.error(f"Error sending multi-photo estimate: {e}", exc_info=True)


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
