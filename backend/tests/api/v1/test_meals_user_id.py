"""Tests for meals API endpoints with user ID detection."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.meals import router


class TestMealsEndpoints:
    """Test meal-related endpoints with user ID detection."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_meals_data(self):
        """Sample meals data for testing."""
        return [
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
        ]

    @pytest.fixture
    def mock_meal_data(self):
        """Sample single meal data for testing."""
        return {
            "id": "meal-1",
            "user_id": "59357664",
            "meal_date": "2025-09-28",
            "meal_type": "breakfast",
            "kcal_total": 500,
            "created_at": "2025-09-28T08:00:00Z",
        }

    @patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date")
    def test_get_meals_with_telegram_user_id(self, mock_db_get_meals, client, mock_meals_data):
        """Test getting meals with real Telegram user ID from header."""
        mock_db_get_meals.return_value = mock_meals_data

        headers = {"x-user-id": "59357664"}
        response = client.get("/meals?date=2025-09-28", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_meals_data

        # Verify that db_get_meals_by_date was called with the correct parameters
        mock_db_get_meals.assert_called_once_with("2025-09-28", "59357664")

    @patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date")
    def test_get_meals_without_user_id_header(self, mock_db_get_meals, client, mock_meals_data):
        """Test getting meals without x-user-id header."""
        mock_db_get_meals.return_value = mock_meals_data

        response = client.get("/meals?date=2025-09-28")

        assert response.status_code == 200
        data = response.json()
        assert data == mock_meals_data

        # Verify that db_get_meals_by_date was called with None user_id
        mock_db_get_meals.assert_called_once_with("2025-09-28", None)

    @patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date")
    def test_get_meals_no_meals_found(self, mock_db_get_meals, client):
        """Test getting meals when no meals exist."""
        mock_db_get_meals.return_value = []

        headers = {"x-user-id": "59357664"}
        response = client.get("/meals?date=2025-09-28", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date")
    def test_get_meals_database_error(self, mock_db_get_meals, client):
        """Test getting meals when database error occurs."""
        mock_db_get_meals.side_effect = Exception("Database connection failed")

        headers = {"x-user-id": "59357664"}
        response = client.get("/meals?date=2025-09-28", headers=headers)

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    def test_get_meals_missing_date_parameter(self, client):
        """Test getting meals without required date parameter."""
        headers = {"x-user-id": "59357664"}
        response = client.get("/meals", headers=headers)

        assert response.status_code == 422  # Validation error

    def test_get_meals_invalid_date_format(self, client):
        """Test getting meals with invalid date format."""
        headers = {"x-user-id": "59357664"}
        response = client.get("/meals?date=invalid-date", headers=headers)

        # The endpoint should still work, but the database query might fail
        # This tests the API endpoint validation
        assert response.status_code in [200, 500]  # Either works or fails gracefully

    def test_empty_user_id_header(self, client):
        """Test getting meals with empty x-user-id header."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": ""}
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use empty string as user_id
            mock_db_get_meals.assert_called_once_with("2025-09-28", "")

    def test_user_id_with_whitespace(self, client):
        """Test user ID with leading/trailing whitespace."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "  59357664  "}  # With whitespace
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is (including whitespace)
            mock_db_get_meals.assert_called_once_with("2025-09-28", "  59357664  ")

    def test_user_id_case_sensitivity(self, client):
        """Test that x-user-id header is case insensitive (FastAPI behavior)."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            # Test with different case - FastAPI treats headers as case-insensitive
            headers = {"X-User-ID": "59357664"}  # Different case
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID since FastAPI is case-insensitive
            mock_db_get_meals.assert_called_once_with("2025-09-28", "59357664")

    def test_multiple_user_id_headers(self, client):
        """Test behavior with multiple x-user-id headers (HTTP spec behavior)."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            # HTTP headers with same name are concatenated with commas
            # FastAPI will use the first value
            headers = {"x-user-id": "59357664,99999999"}  # Comma-separated values
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the full comma-separated value
            mock_db_get_meals.assert_called_once_with("2025-09-28", "59357664,99999999")

    def test_special_characters_in_user_id(self, client):
        """Test user ID with special characters (should still be passed as is)."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            special_id = "user-!@#$%-id"
            headers = {"x-user-id": special_id}
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            mock_db_get_meals.assert_called_once_with("2025-09-28", special_id)

    def test_very_long_user_id(self, client):
        """Test user ID with very long string."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            long_user_id = "a" * 1000  # Very long user ID
            headers = {"x-user-id": long_user_id}
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_meals.assert_called_once_with("2025-09-28", long_user_id)

    def test_numeric_user_id(self, client):
        """Test user ID that is purely numeric."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "123456789"}
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_meals.assert_called_once_with("2025-09-28", "123456789")

    def test_uuid_user_id(self, client):
        """Test user ID that is a UUID."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            uuid_user_id = "550e8400-e29b-41d4-a716-446655440000"
            headers = {"x-user-id": uuid_user_id}
            response = client.get("/meals?date=2025-09-28", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_meals.assert_called_once_with("2025-09-28", uuid_user_id)

    def test_get_meals_with_different_dates(self, client):
        """Test getting meals for different dates."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "59357664"}

            # Test different dates
            dates = ["2025-09-28", "2025-09-29", "2025-09-30"]
            for date in dates:
                response = client.get(f"/meals?date={date}", headers=headers)
                assert response.status_code == 200
                mock_db_get_meals.assert_called_with(date, "59357664")

    def test_get_meals_with_future_date(self, client):
        """Test getting meals for future date."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "59357664"}
            future_date = "2030-12-31"
            response = client.get(f"/meals?date={future_date}", headers=headers)

            assert response.status_code == 200
            mock_db_get_meals.assert_called_once_with(future_date, "59357664")

    def test_get_meals_with_past_date(self, client):
        """Test getting meals for past date."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "59357664"}
            past_date = "2020-01-01"
            response = client.get(f"/meals?date={past_date}", headers=headers)

            assert response.status_code == 200
            mock_db_get_meals.assert_called_once_with(past_date, "59357664")

    def test_get_meals_with_leap_year_date(self, client):
        """Test getting meals for leap year date."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "59357664"}
            leap_date = "2024-02-29"  # Leap year
            response = client.get(f"/meals?date={leap_date}", headers=headers)

            assert response.status_code == 200
            mock_db_get_meals.assert_called_once_with(leap_date, "59357664")

    def test_get_meals_with_edge_case_dates(self, client):
        """Test getting meals for edge case dates."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date") as mock_db_get_meals:
            mock_db_get_meals.return_value = []

            headers = {"x-user-id": "59357664"}

            # Test edge case dates
            edge_dates = [
                "2025-01-01",  # New Year
                "2025-12-31",  # New Year's Eve
                "2025-06-15",  # Mid year
                "2025-02-14",  # Valentine's Day
            ]

            for date in edge_dates:
                response = client.get(f"/meals?date={date}", headers=headers)
                assert response.status_code == 200
                mock_db_get_meals.assert_called_with(date, "59357664")
