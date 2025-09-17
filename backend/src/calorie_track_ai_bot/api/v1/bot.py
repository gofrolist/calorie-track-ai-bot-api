from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ...services.config import TELEGRAM_BOT_TOKEN, USE_WEBHOOK, WEBHOOK_URL, logger
from ...services.db import db_create_photo, db_get_or_create_user
from ...services.queue import enqueue_estimate_job
from ...services.storage import tigris_presign_put
from ...services.telegram import get_bot

router = APIRouter()


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
    """Handle photo messages from user."""
    user_id = message.from_user.get("id") if message.from_user else None
    chat_id = message.chat.get("id") if message.chat else None
    logger.info(f"Handling photo message from user {user_id}")

    if not message.photo:
        logger.warning("Photo message received but no photo data found")
        return

    # Get the highest resolution photo
    photo = max(message.photo, key=lambda x: x.get("file_size", 0))
    file_id = photo.get("file_id")

    if not file_id:
        logger.error("No file_id found in photo message")
        return

    logger.info(f"Processing photo with file_id: {file_id}")

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

        # Download photo from Telegram and upload to Tigris
        bot = get_bot()
        file_info = await bot.get_file(file_id)
        file_path = file_info["file_path"]
        logger.info(f"Downloading photo from Telegram: {file_path}")

        # Download the photo content
        photo_content = await bot.download_file(file_path)

        # Get presigned URL for upload
        storage_key, upload_url = await tigris_presign_put(content_type="image/jpeg")
        logger.info(f"Generated presigned URL for storage key: {storage_key}")

        # Upload photo to Tigris
        async with httpx.AsyncClient() as client:
            upload_response = await client.put(
                upload_url, content=photo_content, headers={"Content-Type": "image/jpeg"}
            )
            upload_response.raise_for_status()
        logger.info(f"Photo uploaded to Tigris with key: {storage_key}")

        # Create photo record in database with actual storage key
        photo_id = await db_create_photo(tigris_key=storage_key, user_id=user_uuid)
        logger.info(f"Photo record created with ID: {photo_id}")

        # Enqueue estimation job
        job_id = await enqueue_estimate_job(photo_id)
        logger.info(f"Estimation job enqueued with ID: {job_id}")

    except Exception as e:
        logger.error(f"Error processing photo message: {e}", exc_info=True)

        # Send error message to user
        if chat_id and TELEGRAM_BOT_TOKEN:
            try:
                bot = get_bot()
                await bot.send_message(
                    chat_id,
                    "❌ Sorry, I encountered an error processing your photo. Please try again later.",
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
