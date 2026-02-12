"""Tests for Feedback Service.

Feature: 005-mini-app-improvements
Tests cover feedback submission logic, timezone handling, and admin notifications.
Uses psycopg3 connection pool mocking (get_pool from database.py).
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from calorie_track_ai_bot.schemas import (
    FeedbackMessageType,
    FeedbackStatus,
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
)
from calorie_track_ai_bot.services.feedback_service import FeedbackService


def _make_mock_pool():
    """Create a mock async connection pool with cursor support.

    pool.connection() is a synchronous call that returns an async context manager,
    so the pool itself is a regular Mock while the connection uses AsyncMock for
    __aenter__/__aexit__ and execute/fetchone.
    """
    mock_pool = Mock()
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_conn.execute = AsyncMock(return_value=mock_cursor)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    ctx.__aexit__ = AsyncMock(return_value=False)
    mock_pool.connection.return_value = ctx

    return mock_pool, mock_conn, mock_cursor


class TestFeedbackServiceSubmission:
    """Test feedback submission logic."""

    @pytest.fixture
    def mock_pool(self):
        """Create a mock psycopg3 connection pool."""
        mock_pool, mock_conn, mock_cursor = _make_mock_pool()

        # Default: _get_user_display returns a user with handle
        mock_cursor.fetchone = AsyncMock(
            return_value={"handle": "testuser", "telegram_id": 123456789}
        )

        return mock_pool, mock_conn, mock_cursor

    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot."""
        mock_bot = Mock()
        mock_bot.send_admin_notification = AsyncMock()
        return mock_bot

    @pytest.fixture
    def feedback_service(self, mock_pool, mock_bot):
        """Create a FeedbackService instance with mocked dependencies."""
        pool, _conn, _cursor = mock_pool

        with (
            patch(
                "calorie_track_ai_bot.services.feedback_service.get_pool",
                new_callable=AsyncMock,
                return_value=pool,
            ),
            patch(
                "calorie_track_ai_bot.services.feedback_service.get_bot",
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
    async def test_submit_feedback_creates_timezone_aware_datetime(self, feedback_service):
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

        response = await feedback_service.submit_feedback(user_id, request)

        assert isinstance(response, FeedbackSubmissionResponse)
        assert isinstance(response.created_at, datetime)
        assert response.created_at.tzinfo is not None
        assert response.created_at.tzinfo == UTC or response.created_at.tzinfo.utcoffset(
            None
        ) == UTC.utcoffset(None)

    @pytest.mark.anyio
    async def test_submit_feedback_saves_to_database(self, feedback_service, mock_pool):
        """Test that feedback is saved to the database with correct fields."""
        _pool, mock_conn, _cursor = mock_pool
        user_id = str(uuid.uuid4())
        request = FeedbackSubmissionRequest(
            message_type=FeedbackMessageType.bug,
            message_content="Found a bug in the app",
            user_context={"page": "/meals", "language": "en"},
        )

        await feedback_service.submit_feedback(user_id, request)

        # Find the INSERT call (first execute call is the INSERT, second is the SELECT in _get_user_display)
        insert_call = None
        for call in mock_conn.execute.call_args_list:
            sql = call[0][0]
            if "INSERT INTO feedback_submissions" in sql:
                insert_call = call
                break

        assert insert_call is not None, "INSERT INTO feedback_submissions was not called"

        params = insert_call[0][1]
        # params is a tuple: (id, user_id, message_type, message_content, user_context, status, admin_notes, created_at, updated_at)
        assert params[1] == user_id
        assert params[2] == "bug"
        assert params[3] == "Found a bug in the app"
        from psycopg.types.json import Json

        assert isinstance(params[4], Json)
        assert params[4].obj == {"page": "/meals", "language": "en"}
        assert params[5] == "new"

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

        mock_bot.send_admin_notification.assert_called_once()
        call_args = mock_bot.send_admin_notification.call_args

        assert call_args[1]["chat_id"] == 123456
        assert "New Feedback Received" in call_args[1]["message"]
        assert "@testuser" in call_args[1]["message"]
        assert "I need help with my account" in call_args[1]["message"]
        # Type, Context, and Status fields should NOT be in message
        assert "Type:" not in call_args[1]["message"]
        assert "Context:" not in call_args[1]["message"]
        assert "Status:" not in call_args[1]["message"]

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
        self, feedback_service, mock_bot, mock_pool
    ):
        """Test that feedback is saved even if admin notification fails."""
        _pool, mock_conn, _cursor = mock_pool

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

        # Verify database INSERT was still called
        insert_called = any(
            "INSERT INTO feedback_submissions" in call[0][0]
            for call in mock_conn.execute.call_args_list
        )
        assert insert_called

    @pytest.mark.anyio
    async def test_submit_feedback_with_notifications_disabled(self):
        """Test that notifications are skipped when disabled."""
        mock_pool, _mock_conn, mock_cursor = _make_mock_pool()
        mock_cursor.fetchone = AsyncMock(
            return_value={"handle": "testuser", "telegram_id": 123456789}
        )
        mock_bot = Mock()
        mock_bot.send_admin_notification = AsyncMock()

        with (
            patch(
                "calorie_track_ai_bot.services.feedback_service.get_pool",
                new_callable=AsyncMock,
                return_value=mock_pool,
            ),
            patch(
                "calorie_track_ai_bot.services.feedback_service.get_bot",
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
    def mock_pool(self):
        """Create a mock psycopg3 connection pool."""
        return _make_mock_pool()

    @pytest.fixture
    def feedback_service(self, mock_pool):
        """Create a FeedbackService instance with mocked dependencies."""
        pool, _conn, _cursor = mock_pool

        with (
            patch(
                "calorie_track_ai_bot.services.feedback_service.get_pool",
                new_callable=AsyncMock,
                return_value=pool,
            ),
            patch(
                "calorie_track_ai_bot.services.feedback_service.get_bot",
                return_value=Mock(),
            ),
        ):
            service = FeedbackService()
            yield service

    @pytest.mark.anyio
    async def test_get_feedback_returns_submission(self, feedback_service, mock_pool):
        """Test that get_feedback retrieves feedback by ID."""
        _pool, _conn, mock_cursor = mock_pool
        feedback_id = uuid.uuid4()
        user_id = str(uuid.uuid4())
        created_at = datetime.now(UTC)

        mock_cursor.fetchone = AsyncMock(
            return_value={
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
        )

        result = await feedback_service.get_feedback(feedback_id)

        assert result is not None
        assert result.id == feedback_id
        assert result.user_id == user_id
        assert result.message_content == "Test feedback"
        assert result.status == FeedbackStatus.new

    @pytest.mark.anyio
    async def test_get_feedback_returns_none_when_not_found(self, feedback_service, mock_pool):
        """Test that get_feedback returns None for non-existent feedback."""
        _pool, _conn, mock_cursor = mock_pool
        feedback_id = uuid.uuid4()

        mock_cursor.fetchone = AsyncMock(return_value=None)

        result = await feedback_service.get_feedback(feedback_id)

        assert result is None

    @pytest.mark.anyio
    async def test_user_display_with_handle(self, feedback_service, mock_pool):
        """Test that user display shows handle when available."""
        _pool, _conn, mock_cursor = mock_pool
        user_id = str(uuid.uuid4())

        mock_cursor.fetchone = AsyncMock(
            return_value={"handle": "john_doe", "telegram_id": 123456789}
        )

        user_display = await feedback_service._get_user_display(user_id)

        assert user_display == "@john\\_doe"

    @pytest.mark.anyio
    async def test_user_display_without_handle(self, feedback_service, mock_pool):
        """Test that user display shows telegram_id when handle is not available."""
        _pool, _conn, mock_cursor = mock_pool
        user_id = str(uuid.uuid4())

        mock_cursor.fetchone = AsyncMock(return_value={"handle": None, "telegram_id": 987654321})

        user_display = await feedback_service._get_user_display(user_id)

        assert user_display == "987654321"

    @pytest.mark.anyio
    async def test_user_display_user_not_found(self, feedback_service, mock_pool):
        """Test that user display falls back to user_id when user not found."""
        _pool, _conn, mock_cursor = mock_pool
        user_id = str(uuid.uuid4())

        mock_cursor.fetchone = AsyncMock(return_value=None)

        user_display = await feedback_service._get_user_display(user_id)

        assert user_display == f"User \\#{user_id[:8]}"

    @pytest.mark.anyio
    async def test_user_display_handles_special_characters(self, feedback_service, mock_pool):
        """Test that user display properly escapes markdown special characters."""
        _pool, _conn, mock_cursor = mock_pool
        user_id = str(uuid.uuid4())

        mock_cursor.fetchone = AsyncMock(
            return_value={"handle": "test_user*bold*", "telegram_id": 123456789}
        )

        user_display = await feedback_service._get_user_display(user_id)

        assert user_display == "@test\\_user\\*bold\\*"
