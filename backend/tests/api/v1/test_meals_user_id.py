"""Tests for meals API endpoints with user ID detection."""

from datetime import UTC
from unittest.mock import patch

import pytest


class TestMealsEndpoints:
    """Test meal-related endpoints with user ID detection."""

    @pytest.fixture
    def mock_meals_data(self):
        """Sample meals data for testing."""
        from datetime import datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        return [
            MealWithPhotos(
                id="550e8400-e29b-41d4-a716-446655440001",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                meal_date="2025-09-28",
                meal_type="breakfast",
                calories=500,
                macronutrients=Macronutrients(protein=20, carbs=60, fats=15),
                photos=[],
                created_at=datetime(2025, 9, 28, 8, 0, 0, tzinfo=UTC),
            ),
            MealWithPhotos(
                id="550e8400-e29b-41d4-a716-446655440002",
                user_id="550e8400-e29b-41d4-a716-446655440000",
                meal_date="2025-09-28",
                meal_type="lunch",
                calories=700,
                macronutrients=Macronutrients(protein=30, carbs=80, fats=25),
                photos=[],
                created_at=datetime(2025, 9, 28, 13, 0, 0, tzinfo=UTC),
            ),
        ]

    @pytest.fixture
    def mock_meal_data(self):
        """Sample single meal data for testing."""
        from datetime import datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        return MealWithPhotos(
            id="550e8400-e29b-41d4-a716-446655440001",
            user_id="550e8400-e29b-41d4-a716-446655440000",
            meal_date="2025-09-28",
            meal_type="breakfast",
            calories=500,
            macronutrients=Macronutrients(protein=20, carbs=60, fat=15),
            photos=[],
            created_at=datetime(2025, 9, 28, 8, 0, 0, tzinfo=UTC),
        )

    def test_get_meals_with_telegram_user_id(
        self, api_client, authenticated_headers, mock_meals_data
    ):
        """Test getting meals with telegram user ID in header."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = mock_meals_data

            response = api_client.get("/api/v1/meals", headers=authenticated_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data["meals"]) == 2
            assert data["meals"][0]["id"] == "550e8400-e29b-41d4-a716-446655440001"
            assert data["meals"][1]["id"] == "550e8400-e29b-41d4-a716-446655440002"

    def test_get_meals_without_user_id_header(self, api_client):
        """Test getting meals without x-user-id header."""
        response = api_client.get("/api/v1/meals")

        assert response.status_code == 401
        assert "Missing x-user-id header" in response.json()["detail"]

    def test_get_meals_no_meals_found(self, api_client, authenticated_headers):
        """Test getting meals when no meals are found."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get("/api/v1/meals", headers=authenticated_headers)

            assert response.status_code == 200
            data = response.json()
            assert len(data["meals"]) == 0

    def test_get_meals_database_error(self, api_client, authenticated_headers):
        """Test getting meals when database error occurs."""
        with patch(
            "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
        ) as mock_db_get_meals:
            mock_db_get_meals.side_effect = Exception("Database connection failed")

            response = api_client.get("/api/v1/meals", headers=authenticated_headers)

            assert response.status_code == 500

    def test_get_meals_missing_date_parameter(self, api_client, authenticated_headers):
        """Test getting meals with missing date parameter."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get("/api/v1/meals", headers=authenticated_headers)

            assert response.status_code == 200
            # Should work without date parameter

    def test_empty_user_id_header(self, api_client):
        """Test getting meals with empty x-user-id header."""
        headers = {"x-user-id": ""}
        response = api_client.get("/api/v1/meals", headers=headers)

        assert response.status_code == 401

    def test_user_id_with_whitespace(self, api_client):
        """Test user ID with leading/trailing whitespace."""
        headers = {"x-user-id": "  59357664  "}
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get("/api/v1/meals", headers=headers)

            assert response.status_code == 200

    def test_user_id_case_sensitivity(self, api_client):
        """Test that x-user-id header is case insensitive (FastAPI behavior)."""
        headers = {"X-User-Id": "59357664"}
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get("/api/v1/meals", headers=headers)

            assert response.status_code == 200

    def test_multiple_user_id_headers(self, api_client):
        """Test behavior with multiple x-user-id headers (HTTP spec behavior)."""
        # Use comma-separated string instead of list for multiple values
        headers = {"x-user-id": "59357664,59357665"}
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get("/api/v1/meals", headers=headers)

            assert response.status_code == 200

    def test_special_characters_in_user_id(self, api_client):
        """Test user ID with special characters (should be rejected)."""
        headers = {"x-user-id": "user@example.com"}
        response = api_client.get("/api/v1/meals", headers=headers)

        assert response.status_code == 401

    def test_very_long_user_id(self, api_client):
        """Test user ID with very long string (should be rejected)."""
        headers = {"x-user-id": "a" * 1000}
        response = api_client.get("/api/v1/meals", headers=headers)

        assert response.status_code == 401

    def test_numeric_user_id(self, api_client):
        """Test user ID that is purely numeric."""
        headers = {"x-user-id": "123456789"}
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get("/api/v1/meals", headers=headers)

            assert response.status_code == 200

    def test_uuid_user_id(self, api_client):
        """Test user ID that is a UUID (should be rejected)."""
        headers = {"x-user-id": "550e8400-e29b-41d4-a716-446655440000"}
        response = api_client.get("/api/v1/meals", headers=headers)

        assert response.status_code == 401

    def test_get_meals_with_different_dates(self, api_client, authenticated_headers):
        """Test getting meals for different dates."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            # Test with specific date
            response = api_client.get(
                "/api/v1/meals?date=2025-09-28", headers=authenticated_headers
            )

            assert response.status_code == 200

    def test_get_meals_with_future_date(self, api_client, authenticated_headers):
        """Test getting meals for future date."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get(
                "/api/v1/meals?date=2030-01-01", headers=authenticated_headers
            )

            assert response.status_code == 200

    def test_get_meals_with_past_date(self, api_client, authenticated_headers):
        """Test getting meals for past date."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get(
                "/api/v1/meals?date=2020-01-01", headers=authenticated_headers
            )

            assert response.status_code == 200

    def test_get_meals_with_leap_year_date(self, api_client, authenticated_headers):
        """Test getting meals for leap year date."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            response = api_client.get(
                "/api/v1/meals?date=2024-02-29", headers=authenticated_headers
            )

            assert response.status_code == 200

    def test_get_meals_with_edge_case_dates(self, api_client, authenticated_headers):
        """Test getting meals for edge case dates."""
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos"
            ) as mock_db_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_id,
        ):
            mock_resolve_user_id.return_value = "550e8400-e29b-41d4-a716-446655440000"
            mock_db_get_meals.return_value = []

            # Test with epoch date
            response = api_client.get(
                "/api/v1/meals?date=1970-01-01", headers=authenticated_headers
            )

            assert response.status_code == 200
