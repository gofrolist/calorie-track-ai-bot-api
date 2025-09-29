from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app


class TestBotWebhook:
    """Test cases for the Telegram bot webhook handler."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_webhook_start_command(self, client):
        """Test webhook handling of /start command."""
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 12345,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {
                    "id": 12345,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private",
                },
                "date": 1640995200,
                "text": "/start",
            },
        }

        with patch("calorie_track_ai_bot.api.v1.bot.db_get_or_create_user") as mock_create_user:
            mock_create_user.return_value = "user-123"

            response = client.post("/bot", json=webhook_data)

            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            mock_create_user.assert_called_once_with(
                telegram_id=12345, handle="testuser", locale="en"
            )

    def test_webhook_photo_message(self, client):
        """Test webhook handling of photo message."""
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 2,
                "from": {
                    "id": 12345,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {
                    "id": 12345,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private",
                },
                "date": 1640995200,
                "photo": [
                    {
                        "file_id": "photo_small",
                        "file_unique_id": "unique_small",
                        "file_size": 1000,
                        "width": 90,
                        "height": 90,
                    },
                    {
                        "file_id": "photo_large",
                        "file_unique_id": "unique_large",
                        "file_size": 50000,
                        "width": 1280,
                        "height": 720,
                    },
                ],
            },
        }

        with (
            patch("calorie_track_ai_bot.api.v1.bot.db_create_photo") as mock_create_photo,
            patch("calorie_track_ai_bot.api.v1.bot.db_get_or_create_user") as mock_get_user,
            patch("calorie_track_ai_bot.api.v1.bot.enqueue_estimate_job") as mock_enqueue,
            patch("calorie_track_ai_bot.api.v1.bot.tigris_presign_put") as mock_presign,
            patch("calorie_track_ai_bot.api.v1.bot.get_bot") as mock_get_bot,
            patch("httpx.AsyncClient") as mock_httpx,
        ):
            # Mock bot methods
            mock_bot = mock_get_bot.return_value

            async def mock_get_file(file_id):
                return {"file_path": "photos/file_123.jpg"}

            async def mock_download_file(file_path):
                return b"fake_image_data"

            mock_bot.get_file = Mock(side_effect=mock_get_file)
            mock_bot.download_file = Mock(side_effect=mock_download_file)

            # Mock httpx client
            mock_client = Mock()
            mock_httpx.return_value.__aenter__.return_value = mock_client

            async def mock_put(url, **kwargs):
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_client.put = Mock(side_effect=mock_put)

            # Mock other services
            mock_get_user.return_value = "user-uuid-123"
            mock_presign.return_value = ("photos/storage_key.jpg", "https://presigned-url.com")
            mock_create_photo.return_value = "photo-123"
            mock_enqueue.return_value = "job-123"

            response = client.post("/bot", json=webhook_data)

            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            mock_get_user.assert_called_once_with(telegram_id=12345, handle="testuser", locale="en")
            mock_bot.get_file.assert_called_once_with("photo_large")
            mock_bot.download_file.assert_called_once_with("photos/file_123.jpg")
            mock_presign.assert_called_once_with(content_type="image/jpeg")
            mock_create_photo.assert_called_once_with(
                tigris_key="photos/storage_key.jpg", user_id="user-uuid-123"
            )
            mock_enqueue.assert_called_once_with("photo-123")

    def test_webhook_text_message(self, client):
        """Test webhook handling of text message."""
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 3,
                "from": {
                    "id": 12345,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {
                    "id": 12345,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private",
                },
                "date": 1640995200,
                "text": "Hello, bot!",
            },
        }

        response = client.post("/bot", json=webhook_data)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_webhook_no_message(self, client):
        """Test webhook handling when no message is present."""
        webhook_data = {"update_id": 123456789}

        response = client.post("/bot", json=webhook_data)

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_webhook_invalid_data(self, client):
        """Test webhook handling with invalid data."""
        response = client.post("/bot", json={"invalid": "data"})

        assert response.status_code == 500

    def test_webhook_photo_processing_error(self, client):
        """Test webhook handling when photo processing fails."""
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 2,
                "from": {
                    "id": 12345,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {
                    "id": 12345,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private",
                },
                "date": 1640995200,
                "photo": [
                    {
                        "file_id": "photo_small",
                        "file_unique_id": "unique_small",
                        "file_size": 1000,
                        "width": 90,
                        "height": 90,
                    }
                ],
            },
        }

        with (
            patch("calorie_track_ai_bot.api.v1.bot.db_create_photo") as mock_create_photo,
            patch("calorie_track_ai_bot.api.v1.bot.db_get_or_create_user") as mock_get_user,
            patch("calorie_track_ai_bot.api.v1.bot.tigris_presign_put") as mock_presign,
            patch("calorie_track_ai_bot.api.v1.bot.get_bot") as mock_get_bot,
            patch("httpx.AsyncClient") as mock_httpx,
        ):
            # Mock bot methods
            mock_bot = mock_get_bot.return_value

            async def mock_get_file(file_id):
                return {"file_path": "photos/file_123.jpg"}

            async def mock_download_file(file_path):
                return b"fake_image_data"

            mock_bot.get_file = Mock(side_effect=mock_get_file)
            mock_bot.download_file = Mock(side_effect=mock_download_file)

            # Mock httpx client
            mock_client = Mock()
            mock_httpx.return_value.__aenter__.return_value = mock_client

            async def mock_put(url, **kwargs):
                mock_response = Mock()
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_client.put = Mock(side_effect=mock_put)

            # Mock other services
            mock_get_user.return_value = "user-uuid-123"
            mock_presign.return_value = ("photos/storage_key.jpg", "https://presigned-url.com")
            mock_create_photo.side_effect = Exception("Database error")

            response = client.post("/bot", json=webhook_data)

            # Should still return 200 to avoid Telegram retries
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    def test_webhook_start_command_error(self, client):
        """Test webhook handling when start command processing fails."""
        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 12345,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {
                    "id": 12345,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private",
                },
                "date": 1640995200,
                "text": "/start",
            },
        }

        with patch("calorie_track_ai_bot.api.v1.bot.db_get_or_create_user") as mock_create_user:
            mock_create_user.side_effect = Exception("Database error")

            response = client.post("/bot", json=webhook_data)

            # Should still return 200 to avoid Telegram retries
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
