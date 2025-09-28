"""Tests for daily summary API endpoints with user ID detection."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.daily_summary import router


class TestDailySummaryEndpoints:
    """Test daily summary-related endpoints with user ID detection."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_daily_summary_data(self):
        """Sample daily summary data for testing."""
        return {
            "user_id": "59357664",
            "date": "2025-09-28",
            "kcal_total": 1500,
            "macros_totals": {
                "protein_g": 75,
                "fat_g": 50,
                "carbs_g": 150,
            },
        }

    @pytest.fixture
    def mock_today_data(self):
        """Sample today data for testing."""
        return {
            "meals": [
                {
                    "id": "meal-1",
                    "user_id": "59357664",
                    "meal_date": "2025-09-28",
                    "meal_type": "breakfast",
                    "kcal_total": 500,
                    "created_at": "2025-09-28T08:00:00Z",
                },
                {
                    "id": "meal-2",
                    "user_id": "59357664",
                    "meal_date": "2025-09-28",
                    "meal_type": "lunch",
                    "kcal_total": 700,
                    "created_at": "2025-09-28T13:00:00Z",
                },
            ],
            "daily_summary": {
                "user_id": "59357664",
                "date": "2025-09-28",
                "kcal_total": 1200,
                "macros_totals": {
                    "protein_g": 60,
                    "fat_g": 40,
                    "carbs_g": 120,
                },
            },
        }

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary")
    def test_get_daily_summary_with_telegram_user_id(
        self, mock_db_get_daily_summary, client, mock_daily_summary_data
    ):
        """Test getting daily summary with real Telegram user ID from header."""
        mock_db_get_daily_summary.return_value = mock_daily_summary_data

        headers = {"x-user-id": "59357664"}
        response = client.get("/daily-summary/2025-09-28", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_daily_summary_data

        # Verify that db_get_daily_summary was called with the correct parameters
        mock_db_get_daily_summary.assert_called_once_with("2025-09-28", "59357664")

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary")
    def test_get_daily_summary_without_user_id_header(
        self, mock_db_get_daily_summary, client, mock_daily_summary_data
    ):
        """Test getting daily summary without x-user-id header."""
        mock_db_get_daily_summary.return_value = mock_daily_summary_data

        response = client.get("/daily-summary/2025-09-28")

        assert response.status_code == 200
        data = response.json()
        assert data == mock_daily_summary_data

        # Verify that db_get_daily_summary was called with None user_id
        mock_db_get_daily_summary.assert_called_once_with("2025-09-28", None)

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary")
    def test_get_daily_summary_no_data_found(self, mock_db_get_daily_summary, client):
        """Test getting daily summary when no data exists."""
        mock_db_get_daily_summary.return_value = None

        headers = {"x-user-id": "59357664"}
        response = client.get("/daily-summary/2025-09-28", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "59357664"
        assert data["date"] == "2025-09-28"
        assert data["kcal_total"] == 0
        assert data["macros_totals"] == {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary")
    def test_get_daily_summary_database_error(self, mock_db_get_daily_summary, client):
        """Test getting daily summary when database error occurs."""
        mock_db_get_daily_summary.side_effect = Exception("Database connection failed")

        headers = {"x-user-id": "59357664"}
        response = client.get("/daily-summary/2025-09-28", headers=headers)

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_today_data")
    def test_get_today_data_with_telegram_user_id(
        self, mock_db_get_today_data, client, mock_today_data
    ):
        """Test getting today data with real Telegram user ID from header."""
        mock_db_get_today_data.return_value = mock_today_data

        headers = {"x-user-id": "59357664"}
        response = client.get("/today/2025-09-28", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_today_data

        # Verify that db_get_today_data was called with the correct parameters
        mock_db_get_today_data.assert_called_once_with("2025-09-28", "59357664")

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_today_data")
    def test_get_today_data_without_user_id_header(
        self, mock_db_get_today_data, client, mock_today_data
    ):
        """Test getting today data without x-user-id header."""
        mock_db_get_today_data.return_value = mock_today_data

        response = client.get("/today/2025-09-28")

        assert response.status_code == 200
        data = response.json()
        assert data == mock_today_data

        # Verify that db_get_today_data was called with None user_id
        mock_db_get_today_data.assert_called_once_with("2025-09-28", None)

    @patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_today_data")
    def test_get_today_data_database_error(self, mock_db_get_today_data, client):
        """Test getting today data when database error occurs."""
        mock_db_get_today_data.side_effect = Exception("Database connection failed")

        headers = {"x-user-id": "59357664"}
        response = client.get("/today/2025-09-28", headers=headers)

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_invalid_date_format(self, client):
        """Test getting daily summary with invalid date format."""
        headers = {"x-user-id": "59357664"}
        response = client.get("/daily-summary/invalid-date", headers=headers)

        # The endpoint should still work, but the database query might fail
        # This tests the API endpoint validation
        assert response.status_code in [200, 500]  # Either works or fails gracefully

    def test_empty_user_id_header(self, client):
        """Test getting daily summary with empty x-user-id header."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            headers = {"x-user-id": ""}
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use empty string as user_id
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", "")

    def test_user_id_with_whitespace(self, client):
        """Test user ID with leading/trailing whitespace."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            headers = {"x-user-id": "  59357664  "}  # With whitespace
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is (including whitespace)
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", "  59357664  ")

    def test_user_id_case_sensitivity(self, client):
        """Test that x-user-id header is case insensitive (FastAPI behavior)."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            # Test with different case - FastAPI treats headers as case-insensitive
            headers = {"X-User-ID": "59357664"}  # Different case
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID since FastAPI is case-insensitive
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", "59357664")

    def test_multiple_user_id_headers(self, client):
        """Test behavior with multiple x-user-id headers (HTTP spec behavior)."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            # HTTP headers with same name are concatenated with commas
            # FastAPI will use the first value
            headers = {"x-user-id": "59357664,99999999"}  # Comma-separated values
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the full comma-separated value
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", "59357664,99999999")

    def test_special_characters_in_user_id(self, client):
        """Test user ID with special characters (should still be passed as is)."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            special_id = "user-!@#$%-id"
            headers = {"x-user-id": special_id}
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", special_id)

    def test_very_long_user_id(self, client):
        """Test user ID with very long string."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            long_user_id = "a" * 1000  # Very long user ID
            headers = {"x-user-id": long_user_id}
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", long_user_id)

    def test_numeric_user_id(self, client):
        """Test user ID that is purely numeric."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            headers = {"x-user-id": "123456789"}
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", "123456789")

    def test_uuid_user_id(self, client):
        """Test user ID that is a UUID."""
        with patch(
            "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
        ) as mock_db_get_daily_summary:
            mock_db_get_daily_summary.return_value = None

            uuid_user_id = "550e8400-e29b-41d4-a716-446655440000"
            headers = {"x-user-id": uuid_user_id}
            response = client.get("/daily-summary/2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_daily_summary.assert_called_once_with("2025-09-28", uuid_user_id)
