"""Tests for meals API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.meals import router


class TestMealsEndpoints:
    """Test meal-related endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_manual_success(self, mock_db_create, client):
        """Test successful manual meal creation."""
        mock_db_create.return_value = {"meal_id": "meal123"}

        payload = {
            "meal_date": "2024-01-01",
            "meal_type": "breakfast",
            "kcal_total": 300.5,
            "macros": {"protein": 20, "carbs": 30, "fat": 10},
        }

        response = client.post("/meals", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "meal_id" in data
        assert data["meal_id"] == "meal123"

    @patch("calorie_track_ai_bot.services.db.resolve_user_id")
    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_estimate")
    def test_create_meal_from_estimate_success(self, mock_db_create, mock_resolve_user_id, client):
        """Test successful meal creation from estimate."""
        mock_resolve_user_id.return_value = "user-uuid-123"
        mock_db_create.return_value = {"meal_id": "meal456"}

        payload = {
            "meal_date": "2024-01-01",
            "meal_type": "lunch",
            "estimate_id": "estimate123",
            "overrides": {"kcal_total": 450},
        }

        response = client.post("/meals", json=payload, headers={"x-user-id": "123456789"})

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "meal_id" in data
        assert data["meal_id"] == "meal456"

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_manual_without_macros(self, mock_db_create, client):
        """Test manual meal creation without macros."""
        mock_db_create.return_value = {"meal_id": "meal789"}

        payload = {
            "meal_date": "2024-01-01",
            "meal_type": "dinner",
            "kcal_total": 500.0,
            # No macros field
        }

        response = client.post("/meals", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["meal_id"] == "meal789"

    @patch("calorie_track_ai_bot.services.db.resolve_user_id")
    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_estimate")
    def test_create_meal_from_estimate_without_overrides(
        self, mock_db_create, mock_resolve_user_id, client
    ):
        """Test meal creation from estimate without overrides."""
        mock_resolve_user_id.return_value = "user-uuid-123"
        mock_db_create.return_value = {"meal_id": "meal456"}
        mock_db_create.return_value = {"meal_id": "meal999"}

        payload = {
            "meal_date": "2024-01-01",
            "meal_type": "snack",
            "estimate_id": "estimate456",
            # No overrides field
        }

        response = client.post("/meals", json=payload, headers={"x-user-id": "123456789"})

        assert response.status_code == 200
        data = response.json()
        assert data["meal_id"] == "meal999"

    def test_create_meal_missing_required_fields(self, client):
        """Test meal creation with missing required fields."""
        # Missing meal_date
        payload = {"meal_type": "breakfast", "kcal_total": 300.5}

        response = client.post("/meals", json=payload)
        assert response.status_code == 422

    def test_create_meal_invalid_data_types(self, client):
        """Test meal creation with invalid data types."""
        # kcal_total should be number
        payload = {
            "meal_date": "2024-01-01",
            "meal_type": "breakfast",
            "kcal_total": "invalid",  # Should be number
        }

        response = client.post("/meals", json=payload)
        assert response.status_code == 422

    def test_create_meal_invalid_meal_type(self, client):
        """Test meal creation with invalid meal type."""
        payload = {
            "meal_date": "2024-01-01",
            "meal_type": "invalid_type",  # Not in enum
            "kcal_total": 300.5,
        }

        response = client.post("/meals", json=payload)
        assert response.status_code == 422

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_manual_db_error(self, mock_db_create, client):
        """Test manual meal creation when database operation fails."""
        mock_db_create.side_effect = Exception("Database Error")

        payload = {"meal_date": "2024-01-01", "meal_type": "breakfast", "kcal_total": 300.5}

        response = client.post("/meals", json=payload)
        assert response.status_code == 500

    @patch("calorie_track_ai_bot.services.db.resolve_user_id")
    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_estimate")
    def test_create_meal_from_estimate_db_error(self, mock_db_create, mock_resolve_user_id, client):
        """Test meal creation from estimate when database operation fails."""
        mock_resolve_user_id.return_value = "user-uuid-123"
        mock_db_create.side_effect = Exception("Database Error")

        payload = {"meal_date": "2024-01-01", "meal_type": "lunch", "estimate_id": "estimate123"}

        response = client.post("/meals", json=payload, headers={"x-user-id": "123456789"})
        assert response.status_code == 500

    def test_meals_endpoint_methods(self, client):
        """Test that meals endpoint handles different HTTP methods correctly."""
        # GET /meals without date parameter should return 422 (validation error)
        get_response = client.get("/meals")
        assert (
            get_response.status_code == 422
        )  # Unprocessable Entity (missing required query param)

        # PUT /meals should return 405 (Method Not Allowed)
        put_response = client.put("/meals")
        assert put_response.status_code == 405

        # DELETE /meals should return 405 (Method Not Allowed)
        delete_response = client.delete("/meals")
        assert delete_response.status_code == 405

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_content_type(self, mock_db_create, client):
        """Test that create meal returns JSON content type."""
        mock_db_create.return_value = {"meal_id": "meal456"}
        mock_db_create.return_value = {"meal_id": "meal123"}

        payload = {"meal_date": "2024-01-01", "meal_type": "breakfast", "kcal_total": 300.5}

        response = client.post("/meals", json=payload)
        assert response.headers["content-type"] == "application/json"

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_response_structure(self, mock_db_create, client):
        """Test that create meal returns consistent response structure."""
        mock_db_create.return_value = {"meal_id": "meal456"}
        mock_db_create.return_value = {"meal_id": "meal123"}

        payload = {"meal_date": "2024-01-01", "meal_type": "breakfast", "kcal_total": 300.5}

        response = client.post("/meals", json=payload)
        data = response.json()

        # Should be valid JSON
        assert isinstance(data, dict)

        # Should have required fields
        assert "meal_id" in data

        # meal_id should be a string
        assert isinstance(data["meal_id"], str)

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_meal_types(self, mock_db_create, client):
        """Test meal creation with different meal types."""
        mock_db_create.return_value = {"meal_id": "meal456"}
        mock_db_create.return_value = {"meal_id": "meal123"}

        meal_types = ["breakfast", "lunch", "dinner", "snack"]

        for meal_type in meal_types:
            payload = {"meal_date": "2024-01-01", "meal_type": meal_type, "kcal_total": 300.5}

            response = client.post("/meals", json=payload)
            assert response.status_code == 200

    @patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual")
    def test_create_meal_date_formats(self, mock_db_create, client):
        """Test meal creation with different date formats."""
        mock_db_create.return_value = {"meal_id": "meal456"}
        mock_db_create.return_value = {"meal_id": "meal123"}

        date_formats = ["2024-01-01", "2024-12-31", "2023-06-15"]

        for meal_date in date_formats:
            payload = {"meal_date": meal_date, "meal_type": "breakfast", "kcal_total": 300.5}

            response = client.post("/meals", json=payload)
            assert response.status_code == 200
