from typing import Any

import httpx

from .config import TELEGRAM_BOT_TOKEN, logger


class TelegramBot:
    """Telegram Bot API client for sending messages and managing webhooks."""

    def __init__(self, token: str | None = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        if not self.token:
            raise ValueError("Telegram bot token is required")

        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
        reply_to_message_id: int | None = None,
    ) -> dict[str, Any]:
        """Send a text message to a chat."""
        url = f"{self.base_url}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id

        logger.debug(f"Sending message to chat {chat_id}: {text[:100]}...")

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info(f"Message sent successfully to chat {chat_id}")
                return result["result"]
            else:
                logger.error(f"Failed to send message: {result.get('description')}")
                raise Exception(f"Telegram API error: {result.get('description')}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    async def send_photo(
        self, chat_id: int, photo: str, caption: str | None = None, parse_mode: str = "HTML"
    ) -> dict[str, Any]:
        """Send a photo to a chat."""
        url = f"{self.base_url}/sendPhoto"
        data = {"chat_id": chat_id, "photo": photo}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = parse_mode

        logger.debug(f"Sending photo to chat {chat_id}")

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info(f"Photo sent successfully to chat {chat_id}")
                return result["result"]
            else:
                logger.error(f"Failed to send photo: {result.get('description')}")
                raise Exception(f"Telegram API error: {result.get('description')}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error sending photo: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            raise

    async def set_webhook(self, webhook_url: str) -> bool:
        """Set the webhook URL for the bot."""
        url = f"{self.base_url}/setWebhook"
        data = {"url": webhook_url}

        logger.info(f"Setting webhook URL: {webhook_url}")

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info("Webhook set successfully")
                return True
            else:
                logger.error(f"Failed to set webhook: {result.get('description')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"HTTP error setting webhook: {e}")
            return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    async def get_webhook_info(self) -> dict[str, Any]:
        """Get current webhook information."""
        url = f"{self.base_url}/getWebhookInfo"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                return result["result"]
            else:
                logger.error(f"Failed to get webhook info: {result.get('description')}")
                return {}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting webhook info: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {}

    async def delete_webhook(self) -> bool:
        """Delete the current webhook."""
        url = f"{self.base_url}/deleteWebhook"

        logger.info("Deleting webhook")

        try:
            response = await self.client.post(url)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info("Webhook deleted successfully")
                return True
            else:
                logger.error(f"Failed to delete webhook: {result.get('description')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"HTTP error deleting webhook: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False

    async def get_file(self, file_id: str) -> dict[str, Any]:
        """Get file information from Telegram."""
        url = f"{self.base_url}/getFile"
        data = {"file_id": file_id}

        logger.debug(f"Getting file info for file_id: {file_id}")

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                logger.info(f"File info retrieved for file_id: {file_id}")
                return result["result"]
            else:
                logger.error(f"Failed to get file info: {result.get('description')}")
                raise Exception(f"Telegram API error: {result.get('description')}")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting file info: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            raise

    async def download_file(self, file_path: str) -> bytes:
        """Download file content from Telegram."""
        file_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"

        logger.debug(f"Downloading file from: {file_url}")

        try:
            response = await self.client.get(file_url)
            response.raise_for_status()

            logger.info(f"File downloaded successfully: {file_path}")
            return response.content

        except httpx.HTTPError as e:
            logger.error(f"HTTP error downloading file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


# Global bot instance
bot: TelegramBot | None = None


def get_bot() -> TelegramBot:
    """Get the global bot instance."""
    global bot
    if bot is None:
        bot = TelegramBot()
    return bot
