import asyncio
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...services.config import TELEGRAM_BOT_TOKEN, USE_WEBHOOK, WEBHOOK_URL, logger
from ...services.db import db_create_photo, db_get_or_create_user
from ...services.queue import enqueue_estimate_job
from ...services.storage import tigris_presign_put
from ...services.telegram import (
    get_bot,
    get_photo_limit_message,
)

router = APIRouter()

# Media group aggregation: {media_group_id: {photos: [], caption: str, task: Task}}
media_groups: dict[str, dict[str, Any]] = {}


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict[str, Any] | None = None


class TelegramMessage(BaseModel):
    message_id: int
    from_user: dict[str, Any] | None = Field(None, alias="from")
    chat: dict[str, Any] | None = None
    date: int
    text: str | None = None
    photo: list[dict[str, Any]] | None = None
    caption: str | None = None
    media_group_id: str | None = None


@router.post("/bot")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates."""
    try:
        # Parse the incoming webhook data
        data = await request.json()
        logger.info(f"Received Telegram webhook: {data}")

        update = TelegramUpdate(**data)

        if not update.message:
            logger.debug("No message in update, skipping")
            return {"status": "ok"}

        message = TelegramMessage(**update.message)
        logger.info(
            f"Processing message from user {message.from_user.get('id') if message.from_user else 'unknown'}"
        )

        # Handle /start command
        if message.text and message.text.startswith("/start"):
            try:
                await handle_start_command(message)
            except Exception as e:
                logger.error(f"Error handling start command: {e}", exc_info=True)
            return {"status": "ok"}

        # Handle photo messages
        if message.photo:
            try:
                await handle_photo_message(message)
            except Exception as e:
                logger.error(f"Error handling photo message: {e}", exc_info=True)
            return {"status": "ok"}

        # Handle other text messages
        if message.text:
            try:
                await handle_text_message(message)
            except Exception as e:
                logger.error(f"Error handling text message: {e}", exc_info=True)
            return {"status": "ok"}

        logger.info("Unhandled message type received")
        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


async def handle_start_command(message: TelegramMessage) -> None:
    """Handle /start command from user."""
    user_id = message.from_user.get("id") if message.from_user else None
    username = message.from_user.get("username") if message.from_user else None
    chat_id = message.chat.get("id") if message.chat else None

    logger.info(f"Handling /start command from user {user_id} (@{username})")

    # Create or get user in database
    if user_id:
        await db_get_or_create_user(
            telegram_id=user_id,
            handle=username,
            locale="en",  # Default locale
        )
        logger.info(f"User {user_id} created/retrieved from database")

    # Send welcome message back to user
    if chat_id and TELEGRAM_BOT_TOKEN:
        try:
            bot = get_bot()
            welcome_text = (
                "🍎 <b>Welcome to Calorie Track AI!</b>\n\n"
                "I can help you track your calories by analyzing photos of your meals.\n\n"
                "<b>How to use:</b>\n"
                "📸 Send me a photo of your meal\n"
                "🤖 I'll analyze it and estimate the calories\n"
                "📊 Track your daily calorie intake\n\n"
                "Just send me a photo to get started!"
            )
            await bot.send_message(chat_id, welcome_text)
            logger.info(f"Welcome message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
    else:
        logger.warning("Cannot send welcome message: missing chat_id or bot token")

    logger.info("Start command processed successfully")


async def handle_photo_message(message: TelegramMessage) -> None:
    """Handle photo messages from user, supporting multi-photo media groups."""
    user_id = message.from_user.get("id") if message.from_user else None
    media_group_id = message.media_group_id

    logger.info(f"Handling photo message from user {user_id}, media_group_id: {media_group_id}")

    if not message.photo:
        logger.warning("Photo message received but no photo data found")
        return

    # Get the highest resolution photo
    photo = max(message.photo, key=lambda x: x.get("file_size", 0))
    file_id = photo.get("file_id")

    if not file_id:
        logger.error("No file_id found in photo message")
        return

    # If this is part of a media group, aggregate photos
    if media_group_id:
        await handle_media_group_photo(message, media_group_id, file_id)
    else:
        # Single photo - process immediately
        await process_single_photo(message, file_id)


async def handle_media_group_photo(
    message: TelegramMessage, media_group_id: str, file_id: str
) -> None:
    """Aggregate photos from media group before processing."""
    user_id = message.from_user.get("id") if message.from_user else None
    chat_id = message.chat.get("id") if message.chat else None

    # Initialize or update media group
    if media_group_id not in media_groups:
        media_groups[media_group_id] = {
            "photos": [],
            "caption": message.caption,
            "message": message,
            "processing_task": None,
        }
        logger.info(f"Created new media group: {media_group_id}")

    # Add photo to group
    media_groups[media_group_id]["photos"].append(file_id)
    photo_count = len(media_groups[media_group_id]["photos"])
    logger.info(f"Added photo to media group {media_group_id}, count: {photo_count}")

    # Check 5-photo limit
    if photo_count > 5:
        logger.warning(f"Media group {media_group_id} exceeds 5-photo limit")

        # Send limit message to user (only once)
        if photo_count == 6 and chat_id:
            try:
                bot = get_bot()
                limit_message = get_photo_limit_message()
                await bot.send_message(
                    chat_id,
                    limit_message,
                    reply_to_message_id=message.message_id,
                )
                logger.info(f"Photo limit message sent to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send limit message: {e}")

        # Truncate to 5 photos
        media_groups[media_group_id]["photos"] = media_groups[media_group_id]["photos"][:5]
        return

    # Cancel previous processing task if exists
    if media_groups[media_group_id]["processing_task"]:
        media_groups[media_group_id]["processing_task"].cancel()

    # Schedule processing after 200ms wait (Telegram typically sends photos within this window)
    async def process_after_wait():
        await asyncio.sleep(0.2)  # 200ms wait

        if media_group_id in media_groups:
            group_data = media_groups.pop(media_group_id)
            photo_ids_list = group_data["photos"]
            caption = group_data["caption"]
            original_message = group_data["message"]

            logger.info(
                f"Processing media group {media_group_id} with {len(photo_ids_list)} photos"
            )

            await process_photo_group(
                original_message,
                photo_ids_list,
                caption,
            )

    # Create and store the processing task
    task = asyncio.create_task(process_after_wait())
    media_groups[media_group_id]["processing_task"] = task


async def process_single_photo(message: TelegramMessage, file_id: str) -> None:
    """Process a single photo (no media group)."""
    await process_photo_group(message, [file_id], message.caption)


async def process_photo_group(
    message: TelegramMessage,
    file_ids: list[str],
    description: str | None,
) -> None:
    """Process one or more photos as a single meal."""
    user_id = message.from_user.get("id") if message.from_user else None
    chat_id = message.chat.get("id") if message.chat else None
    logger.info(f"Processing {len(file_ids)} photo(s) from user {user_id}")

    try:
        # Get or create user to get proper UUID
        username = message.from_user.get("username") if message.from_user else None
        user_uuid = None
        if user_id:
            user_uuid = await db_get_or_create_user(
                telegram_id=user_id,
                handle=username,
                locale="en",  # Default locale
            )
            logger.info(f"User {user_id} created/retrieved with UUID: {user_uuid}")

        # Download and upload all photos
        bot = get_bot()
        photo_ids = []

        for idx, file_id in enumerate(file_ids):
            try:
                # Download photo from Telegram
                file_info = await bot.get_file(file_id)
                file_path = file_info["file_path"]
                logger.info(f"Downloading photo {idx + 1}/{len(file_ids)}: {file_path}")

                photo_content = await bot.download_file(file_path)

                # Get presigned URL for upload
                storage_key, upload_url = await tigris_presign_put(content_type="image/jpeg")
                logger.info(f"Generated presigned URL for storage key: {storage_key}")

                # Upload photo to Tigris
                async with httpx.AsyncClient() as client:
                    upload_response = await client.put(
                        upload_url,
                        content=photo_content,
                        headers={"Content-Type": "image/jpeg"},
                    )
                    upload_response.raise_for_status()
                logger.info(f"Photo {idx + 1} uploaded to Tigris")

                # Create photo record in database with display_order
                photo_id = await db_create_photo(
                    tigris_key=storage_key,
                    user_id=user_uuid,
                    display_order=idx,
                    media_group_id=message.media_group_id,
                )
                photo_ids.append(photo_id)
                logger.info(f"Photo record created with ID: {photo_id}")

            except Exception as e:
                logger.error(f"Error processing photo {idx + 1}: {e}", exc_info=True)
                # Continue with other photos

        if not photo_ids:
            raise ValueError("No photos were successfully processed")

        # Enqueue estimation job for all photos
        job_id = await enqueue_estimate_job(photo_ids, description=description)
        logger.info(f"Estimation job enqueued for {len(photo_ids)} photo(s), job ID: {job_id}")

        # Send acknowledgment to user
        if chat_id:
            try:
                bot = get_bot()
                ack_message = (
                    f"📸 Processing {len(photo_ids)} photo{'s' if len(photo_ids) > 1 else ''} "
                    f"for your meal... I'll send you the calorie estimate shortly!"
                )
                await bot.send_message(
                    chat_id,
                    ack_message,
                    reply_to_message_id=message.message_id,
                )
            except Exception as e:
                logger.error(f"Failed to send acknowledgment: {e}")

    except Exception as e:
        logger.error(f"Error processing photo group: {e}", exc_info=True)

        # Send error message to user
        if chat_id and TELEGRAM_BOT_TOKEN:
            try:
                bot = get_bot()
                await bot.send_message(
                    chat_id,
                    "❌ Sorry, I encountered an error processing your photo(s). Please try again later.",
                    reply_to_message_id=message.message_id,
                )
                logger.info(f"Error message sent to user {user_id}")
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")


async def handle_text_message(message: TelegramMessage) -> None:
    """Handle text messages from user."""
    user_id = message.from_user.get("id") if message.from_user else None
    chat_id = message.chat.get("id") if message.chat else None
    text = message.text or ""

    logger.info(f"Handling text message from user {user_id}: {text[:100]}...")

    # Send helpful response for unknown commands
    if chat_id and TELEGRAM_BOT_TOKEN:
        try:
            bot = get_bot()
            response_text = (
                "🤖 I'm a calorie tracking bot!\n\n"
                "Here's what I can do:\n"
                "• Send me <b>/start</b> to get started\n"
                "• Send me a <b>photo of your meal</b> to get calorie estimates\n"
                "• I'll analyze your food and tell you the calories\n\n"
                "Try sending me a photo of your meal! 📸"
            )
            await bot.send_message(chat_id, response_text, reply_to_message_id=message.message_id)
            logger.info(f"Help message sent to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send help message: {e}")

    logger.info(f"Text message processed: {text}")


@router.post("/bot/setup")
async def setup_webhook():
    """Setup Telegram webhook if configured."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN not configured")

    if not USE_WEBHOOK or not WEBHOOK_URL:
        raise HTTPException(status_code=400, detail="Webhook not enabled or URL not configured")

    try:
        bot = get_bot()
        success = await bot.set_webhook(WEBHOOK_URL)

        if success:
            logger.info(f"Webhook set successfully: {WEBHOOK_URL}")
            return {"status": "success", "webhook_url": WEBHOOK_URL}
        else:
            logger.error("Failed to set webhook")
            raise HTTPException(status_code=500, detail="Failed to set webhook")

    except Exception as e:
        logger.error(f"Error setting webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error setting webhook: {e!s}") from e


@router.get("/bot/webhook-info")
async def get_webhook_info():
    """Get current webhook information."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN not configured")

    try:
        bot = get_bot()
        info = await bot.get_webhook_info()
        return {"status": "success", "webhook_info": info}

    except Exception as e:
        logger.error(f"Error getting webhook info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting webhook info: {e!s}") from e


@router.delete("/bot/webhook")
async def delete_webhook():
    """Delete current webhook."""
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=400, detail="TELEGRAM_BOT_TOKEN not configured")

    try:
        bot = get_bot()
        success = await bot.delete_webhook()

        if success:
            logger.info("Webhook deleted successfully")
            return {"status": "success", "message": "Webhook deleted"}
        else:
            logger.error("Failed to delete webhook")
            raise HTTPException(status_code=500, detail="Failed to delete webhook")

    except Exception as e:
        logger.error(f"Error deleting webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting webhook: {e!s}") from e
