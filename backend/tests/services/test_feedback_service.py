"""Tests for Feedback Service.

Feature: 005-mini-app-improvements
Tests cover feedback submission logic, timezone handling, and admin notifications.
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.calorie_track_ai_bot.schemas import (
    FeedbackMessageType,
    FeedbackStatus,
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
)
from src.calorie_track_ai_bot.services.feedback_service import FeedbackService


class TestFeedbackServiceSubmission:
    """Test feedback submission logic."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        mock_sb = Mock()
        mock_table = Mock()
        mock_insert = Mock()
        mock_execute = Mock()

        mock_execute.execute.return_value = Mock(data=[])
        mock_insert.return_value = mock_execute
        mock_table.insert = mock_insert
        mock_sb.table.return_value = mock_table

        return mock_sb

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        mock_bot = Mock()
        mock_bot.send_admin_notification = AsyncMock()
        return mock_bot

    @pytest.fixture
    def feedback_service(self, mock_supabase, mock_bot):
        """Create a FeedbackService instance with mocked dependencies."""
        with (
            patch("src.calorie_track_ai_bot.services.feedback_service.sb", mock_supabase),
            patch(
                "src.calorie_track_ai_bot.services.feedback_service.get_bot",
                return_value=mock_bot,
            ),
            patch.dict(
                "os.environ",
                {
                    "ADMIN_NOTIFICATION_CHAT_ID": "123456",
                    "FEEDBACK_NOTIFICATIONS_ENABLED": "true",
                },
            ),
        ):
            service = FeedbackService()
            yield service

    @pytest.mark.anyio
    async def test_submit_feedback_creates_timezone_aware_datetime(
        self, feedback_service, mock_supabase
    ):
        """Test that feedback submission creates timezone-aware datetime.

        This is a critical test for the bug we fixed where datetime.utcnow()
        created naive datetimes that failed Pydantic validation.
        """
        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.feedback,
            message_content="Test feedback message",
            user_context={"page": "/feedback", "language": "en"},
        )

        # Submit feedback
        response = await feedback_service.submit_feedback(user_id, request)

        # Validate response has timezone-aware datetime
        assert isinstance(response, FeedbackSubmissionResponse)
        assert isinstance(response.created_at, datetime)
        assert response.created_at.tzinfo is not None  # Critical: must have timezone
        assert response.created_at.tzinfo == UTC or response.created_at.tzinfo.utcoffset(
            None
        ) == UTC.utcoffset(None)

    @pytest.mark.anyio
    async def test_submit_feedback_saves_to_database(self, feedback_service, mock_supabase):
        """Test that feedback is saved to the database with correct fields."""
        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.bug,
            message_content="Found a bug in the app",
            user_context={"page": "/meals", "language": "en"},
        )

        await feedback_service.submit_feedback(user_id, request)

        # Verify database insert was called
        mock_supabase.table.assert_called_with("feedback_submissions")
        insert_call = mock_supabase.table.return_value.insert.call_args

        # Validate inserted data
        assert insert_call is not None
        inserted_data = insert_call[0][0]

        assert "id" in inserted_data
        assert inserted_data["user_id"] == user_id
        assert inserted_data["message_type"] == "bug"
        assert inserted_data["message_content"] == "Found a bug in the app"
        assert inserted_data["user_context"] == {"page": "/meals", "language": "en"}
        assert inserted_data["status"] == "new"
        assert "created_at" in inserted_data
        assert "updated_at" in inserted_data

    @pytest.mark.anyio
    async def test_submit_feedback_returns_correct_response(self, feedback_service):
        """Test that feedback submission returns proper response."""
        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.question,
            message_content="How do I track water intake?",
        )

        response = await feedback_service.submit_feedback(user_id, request)

        assert isinstance(response, FeedbackSubmissionResponse)
        assert isinstance(response.id, uuid.UUID)
        assert response.status == FeedbackStatus.new
        assert isinstance(response.created_at, datetime)
        assert response.message == "Thank you! We received your feedback."

    @pytest.mark.anyio
    async def test_submit_feedback_sends_admin_notification(self, feedback_service, mock_bot):
        """Test that admin notification is sent on feedback submission."""
        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.support,
            message_content="I need help with my account",
        )

        await feedback_service.submit_feedback(user_id, request)

        # Verify admin notification was sent
        mock_bot.send_admin_notification.assert_called_once()
        call_args = mock_bot.send_admin_notification.call_args

        assert call_args[1]["chat_id"] == 123456
        assert "New Feedback Received" in call_args[1]["message"]
        assert "SUPPORT" in call_args[1]["message"]
        assert "I need help with my account" in call_args[1]["message"]

    @pytest.mark.anyio
    async def test_submit_feedback_handles_all_message_types(self, feedback_service):
        """Test that all valid message types are handled correctly."""
        user_id = str(uuid.uuid4())
        message_types = [
            FeedbackMessageType.feedback,
            FeedbackMessageType.bug,
            FeedbackMessageType.question,
            FeedbackMessageType.support,
        ]

        for message_type in message_types:
            request = FeedbackSubmissionRequest(
                message_type=message_type,
                message_content=f"Test {message_type.value} message",
            )

            response = await feedback_service.submit_feedback(user_id, request)

            assert response.status == FeedbackStatus.new
            assert isinstance(response.id, uuid.UUID)

    @pytest.mark.anyio
    async def test_submit_feedback_without_user_context(self, feedback_service):
        """Test that user_context is optional."""
        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.feedback,
            message_content="Test feedback without context",
            # user_context is None
        )

        response = await feedback_service.submit_feedback(user_id, request)

        assert isinstance(response, FeedbackSubmissionResponse)
        assert response.status == FeedbackStatus.new

    @pytest.mark.anyio
    async def test_submit_feedback_continues_on_notification_failure(
        self, feedback_service, mock_bot, mock_supabase
    ):
        """Test that feedback is saved even if admin notification fails."""
        # Make admin notification fail
        mock_bot.send_admin_notification.side_effect = Exception("Notification failed")

        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.feedback,
            message_content="Test feedback",
        )

        # Should still succeed and return response
        response = await feedback_service.submit_feedback(user_id, request)

        assert isinstance(response, FeedbackSubmissionResponse)
        assert response.status == FeedbackStatus.new

        # Verify database insert was still called
        mock_supabase.table.assert_called_with("feedback_submissions")

    @pytest.mark.anyio
    async def test_submit_feedback_with_notifications_disabled(self, mock_supabase, mock_bot):
        """Test that notifications are skipped when disabled."""
        with (
            patch("src.calorie_track_ai_bot.services.feedback_service.sb", mock_supabase),
            patch(
                "src.calorie_track_ai_bot.services.feedback_service.get_bot",
                return_value=mock_bot,
            ),
            patch.dict(
                "os.environ",
                {
                    "ADMIN_NOTIFICATION_CHAT_ID": "123456",
                    "FEEDBACK_NOTIFICATIONS_ENABLED": "false",
                },
            ),
        ):
            service = FeedbackService()

            user_id = str(uuid.uuid4())
            request = FeedbackSubmissionRequest(
                message_type=FeedbackMessageType.feedback,
                message_content="Test feedback",
            )

            await service.submit_feedback(user_id, request)

            # Verify notification was NOT sent
            mock_bot.send_admin_notification.assert_not_called()


class TestFeedbackServiceRetrieval:
    """Test feedback retrieval logic."""

    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        mock_sb = Mock()
        return mock_sb

    @pytest.fixture
    def feedback_service(self, mock_supabase):
        """Create a FeedbackService instance with mocked dependencies."""
        with patch("src.calorie_track_ai_bot.services.feedback_service.sb", mock_supabase):
            mock_bot = Mock()
            with patch(
                "src.calorie_track_ai_bot.services.feedback_service.get_bot",
                return_value=mock_bot,
            ):
                service = FeedbackService()
                yield service

    @pytest.mark.anyio
    async def test_get_feedback_returns_submission(self, feedback_service, mock_supabase):
        """Test that get_feedback retrieves feedback by ID."""
        feedback_id = uuid.uuid4()
        user_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)

        # Mock database response
        mock_data = {
            "id": str(feedback_id),
            "user_id": user_id,
            "message_type": "feedback",
            "message_content": "Test feedback",
            "user_context": {"page": "/feedback"},
            "status": "new",
            "admin_notes": None,
            "created_at": created_at.isoformat(),
            "updated_at": created_at.isoformat(),
        }

        mock_result = Mock()
        mock_result.data = [mock_data]

        mock_execute = Mock()
        mock_execute.execute.return_value = mock_result

        mock_eq = Mock()
        mock_eq.eq.return_value = mock_execute

        mock_select = Mock()
        mock_select.select.return_value = mock_eq

        mock_supabase.table.return_value = mock_select

        # Get feedback
        result = await feedback_service.get_feedback(feedback_id)

        assert result is not None
        assert result.id == feedback_id
        assert result.user_id == user_id
        assert result.message_content == "Test feedback"
        assert result.status == FeedbackStatus.new

    @pytest.mark.anyio
    async def test_get_feedback_returns_none_when_not_found(self, feedback_service, mock_supabase):
        """Test that get_feedback returns None for non-existent feedback."""
        feedback_id = uuid.uuid4()

        # Mock empty database response
        mock_result = Mock()
        mock_result.data = []

        mock_execute = Mock()
        mock_execute.execute.return_value = mock_result

        mock_eq = Mock()
        mock_eq.eq.return_value = mock_execute

        mock_select = Mock()
        mock_select.select.return_value = mock_eq

        mock_supabase.table.return_value = mock_select

        result = await feedback_service.get_feedback(feedback_id)

        assert result is None
