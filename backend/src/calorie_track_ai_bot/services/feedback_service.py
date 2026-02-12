"""Feedback Service - User feedback submission and management.

Feature: 005-mini-app-improvements
Handles storage and notification of user feedback, bugs, questions, and support requests.
"""

import os
from datetime import UTC, datetime
from uuid import UUID, uuid4

from psycopg.types.json import Json

from ..schemas import (
    FeedbackMessageType,
    FeedbackStatus,
    FeedbackSubmission,
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
)
from .config import logger
from .database import get_pool
from .telegram import get_bot


class FeedbackService:
    """Service for managing user feedback submissions."""

    def __init__(self):
        self.bot = get_bot()
        self.admin_chat_id = os.getenv("ADMIN_NOTIFICATION_CHAT_ID")
        self.notifications_enabled = (
            os.getenv("FEEDBACK_NOTIFICATIONS_ENABLED", "true").lower() == "true"
        )

    async def submit_feedback(
        self,
        user_id: str,
        request: FeedbackSubmissionRequest,
    ) -> FeedbackSubmissionResponse:
        """Submit user feedback and send admin notification."""
        feedback_id = uuid4()
        now = datetime.now(UTC)

        feedback_data = {
            "id": str(feedback_id),
            "user_id": user_id,
            "message_type": request.message_type.value,
            "message_content": request.message_content,
            "user_context": Json(request.user_context)
            if request.user_context is not None
            else None,
            "status": FeedbackStatus.new.value,
            "admin_notes": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        try:
            pool = await get_pool()
            async with pool.connection() as conn:
                await conn.execute(
                    """INSERT INTO feedback_submissions
                       (id, user_id, message_type, message_content, user_context,
                        status, admin_notes, created_at, updated_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        feedback_data["id"],
                        feedback_data["user_id"],
                        feedback_data["message_type"],
                        feedback_data["message_content"],
                        feedback_data["user_context"],
                        feedback_data["status"],
                        feedback_data["admin_notes"],
                        feedback_data["created_at"],
                        feedback_data["updated_at"],
                    ),
                )

            logger.info(
                f"Feedback submitted successfully: {feedback_id}",
                extra={
                    "feedback_id": str(feedback_id),
                    "user_id": user_id,
                    "message_type": request.message_type.value,
                },
            )

            if self.notifications_enabled and self.admin_chat_id:
                await self._send_admin_notification(
                    feedback_id=feedback_id,
                    user_id=user_id,
                    message_type=request.message_type,
                    message_content=request.message_content,
                    user_context=request.user_context,
                    created_at=now,
                )

            return FeedbackSubmissionResponse(
                id=feedback_id,
                status=FeedbackStatus.new,
                created_at=now,
                message="Thank you! We received your feedback.",
            )

        except Exception as e:
            logger.error(
                f"Failed to submit feedback: {e}",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    async def _send_admin_notification(
        self,
        feedback_id: UUID,
        user_id: str,
        message_type: FeedbackMessageType,
        message_content: str,
        user_context: dict | None,
        created_at: datetime,
    ) -> None:
        """Send Telegram notification to admin chat/channel."""
        if not self.admin_chat_id:
            logger.warning("ADMIN_NOTIFICATION_CHAT_ID not configured, skipping notification")
            return

        try:
            chat_id = int(self.admin_chat_id)
            user_display = await self._get_user_display(user_id)

            message = f"""🔔 *New Feedback Received*

👤 *From:* {user_display}
🕒 *Time:* {created_at.strftime("%Y-%m-%d %H:%M:%S UTC")}

*Message:*
{message_content}

*ID:* `{feedback_id}`
"""

            await self.bot.send_admin_notification(
                chat_id=chat_id,
                message=message,
                parse_mode="Markdown",
            )

            logger.info(
                f"Admin notification sent for feedback {feedback_id}",
                extra={"feedback_id": str(feedback_id), "admin_chat_id": chat_id},
            )

        except ValueError:
            logger.error(
                f"Invalid ADMIN_NOTIFICATION_CHAT_ID: {self.admin_chat_id}",
                extra={"feedback_id": str(feedback_id)},
            )
        except Exception as e:
            logger.error(
                f"Failed to send admin notification for feedback {feedback_id}: {e}",
                extra={"feedback_id": str(feedback_id), "error": str(e)},
                exc_info=True,
            )

    async def _get_user_display(self, user_id: str) -> str:
        """Get user display name from database."""
        try:
            pool = await get_pool()
            async with pool.connection() as conn:
                cur = await conn.execute(
                    "SELECT handle, telegram_id FROM users WHERE id = %s", (user_id,)
                )
                row = await cur.fetchone()

            if row:
                user_data = dict(row)
                handle = user_data.get("handle")
                telegram_id = user_data.get("telegram_id")

                if handle:
                    escaped_handle = (
                        handle.replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
                    )
                    return f"@{escaped_handle}"
                elif telegram_id:
                    return str(telegram_id)

            return f"User \\#{user_id[:8]}"

        except Exception as e:
            logger.error(
                f"Failed to get user display for {user_id}: {e}",
                extra={"user_id": user_id, "error": str(e)},
            )
            return f"User \\#{user_id[:8]}"

    async def get_feedback(self, feedback_id: UUID) -> FeedbackSubmission | None:
        """Retrieve feedback submission by ID (admin only)."""
        try:
            pool = await get_pool()
            async with pool.connection() as conn:
                cur = await conn.execute(
                    "SELECT * FROM feedback_submissions WHERE id = %s", (str(feedback_id),)
                )
                row = await cur.fetchone()

            if row:
                data = dict(row)
                return FeedbackSubmission(
                    id=UUID(str(data["id"])),
                    user_id=data["user_id"],
                    message_type=FeedbackMessageType(data["message_type"]),
                    message_content=data["message_content"],
                    user_context=data.get("user_context"),
                    status=FeedbackStatus(data["status"]),
                    admin_notes=data.get("admin_notes"),
                    created_at=datetime.fromisoformat(str(data["created_at"])),
                    updated_at=datetime.fromisoformat(str(data["updated_at"])),
                )

            return None

        except Exception as e:
            logger.error(
                f"Failed to retrieve feedback {feedback_id}: {e}",
                extra={"feedback_id": str(feedback_id), "error": str(e)},
                exc_info=True,
            )
            return None


# Global service instance
_feedback_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    """Get the global feedback service instance."""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
