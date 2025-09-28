"""Tests for goals API endpoints with user ID detection."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.goals import router


class TestGoalsEndpoints:
    """Test goal-related endpoints with user ID detection."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.fixture
    def mock_goal_data(self):
        """Sample goal data for testing."""
        return {
            "id": "goal-123",
            "user_id": "59357664",
            "daily_kcal_target": 2000,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }

    @patch("calorie_track_ai_bot.api.v1.goals.db_get_goal")
    def test_get_goal_with_telegram_user_id(self, mock_db_get_goal, client, mock_goal_data):
        """Test getting goal with real Telegram user ID from header."""
        mock_db_get_goal.return_value = mock_goal_data

        headers = {"x-user-id": "59357664"}
        response = client.get("/goals", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_get_goal was called with the correct user ID
        mock_db_get_goal.assert_called_once_with("59357664")

    @patch("calorie_track_ai_bot.api.v1.goals.db_get_goal")
    def test_get_goal_without_user_id_header(self, mock_db_get_goal, client, mock_goal_data):
        """Test getting goal without x-user-id header falls back to dummy ID."""
        mock_db_get_goal.return_value = mock_goal_data

        response = client.get("/goals")

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_get_goal was called with the dummy user ID
        mock_db_get_goal.assert_called_once_with("00000000-0000-0000-0000-000000000001")

    @patch("calorie_track_ai_bot.api.v1.goals.db_get_goal")
    def test_get_goal_with_empty_user_id_header(self, mock_db_get_goal, client, mock_goal_data):
        """Test getting goal with empty x-user-id header falls back to dummy ID."""
        mock_db_get_goal.return_value = mock_goal_data

        headers = {"x-user-id": ""}
        response = client.get("/goals", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_get_goal was called with the dummy user ID
        mock_db_get_goal.assert_called_once_with("00000000-0000-0000-0000-000000000001")

    @patch("calorie_track_ai_bot.api.v1.goals.db_get_goal")
    def test_get_goal_no_goal_found(self, mock_db_get_goal, client):
        """Test getting goal when no goal exists for user."""
        mock_db_get_goal.return_value = None

        headers = {"x-user-id": "59357664"}
        response = client.get("/goals", headers=headers)

        assert response.status_code == 200
        assert response.json() is None

        mock_db_get_goal.assert_called_once_with("59357664")

    @patch("calorie_track_ai_bot.api.v1.goals.db_get_goal")
    def test_get_goal_database_error(self, mock_db_get_goal, client):
        """Test getting goal when database error occurs."""
        mock_db_get_goal.side_effect = Exception("Database connection failed")

        headers = {"x-user-id": "59357664"}
        response = client.get("/goals", headers=headers)

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    @patch("calorie_track_ai_bot.api.v1.goals.db_get_goal")
    def test_get_goal_table_not_found(self, mock_db_get_goal, client):
        """Test getting goal when table doesn't exist."""
        mock_db_get_goal.side_effect = Exception("Could not find the table")

        headers = {"x-user-id": "59357664"}
        response = client.get("/goals", headers=headers)

        assert response.status_code == 200
        assert response.json() is None

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_create_goal_with_telegram_user_id(self, mock_db_create_goal, client, mock_goal_data):
        """Test creating goal with real Telegram user ID from header."""
        mock_db_create_goal.return_value = mock_goal_data

        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 2000}
        response = client.post("/goals", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_create_or_update_goal was called with the correct user ID
        mock_db_create_goal.assert_called_once_with("59357664", 2000)

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_create_goal_without_user_id_header(self, mock_db_create_goal, client, mock_goal_data):
        """Test creating goal without x-user-id header falls back to dummy ID."""
        mock_db_create_goal.return_value = mock_goal_data

        payload = {"daily_kcal_target": 2000}
        response = client.post("/goals", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_create_or_update_goal was called with the dummy user ID
        mock_db_create_goal.assert_called_once_with("00000000-0000-0000-0000-000000000001", 2000)

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_create_goal_database_error(self, mock_db_create_goal, client):
        """Test creating goal when database error occurs."""
        mock_db_create_goal.side_effect = Exception("Database connection failed")

        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 2000}
        response = client.post("/goals", json=payload, headers=headers)

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_create_goal_table_not_found(self, mock_db_create_goal, client):
        """Test creating goal when table doesn't exist."""
        mock_db_create_goal.side_effect = Exception("Could not find the table")

        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 2000}
        response = client.post("/goals", json=payload, headers=headers)

        assert response.status_code == 503
        assert "Goals feature not yet available" in response.json()["detail"]

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_update_goal_with_telegram_user_id(self, mock_db_create_goal, client, mock_goal_data):
        """Test updating goal with real Telegram user ID from header."""
        mock_db_create_goal.return_value = mock_goal_data

        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 2500}
        response = client.patch("/goals", json=payload, headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_create_or_update_goal was called with the correct user ID
        mock_db_create_goal.assert_called_once_with("59357664", 2500)

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_update_goal_without_user_id_header(self, mock_db_create_goal, client, mock_goal_data):
        """Test updating goal without x-user-id header falls back to dummy ID."""
        mock_db_create_goal.return_value = mock_goal_data

        payload = {"daily_kcal_target": 2500}
        response = client.patch("/goals", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data == mock_goal_data

        # Verify that db_create_or_update_goal was called with the dummy user ID
        mock_db_create_goal.assert_called_once_with("00000000-0000-0000-0000-000000000001", 2500)

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_update_goal_database_error(self, mock_db_create_goal, client):
        """Test updating goal when database error occurs."""
        mock_db_create_goal.side_effect = Exception("Database connection failed")

        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 2500}
        response = client.patch("/goals", json=payload, headers=headers)

        assert response.status_code == 500
        assert "Database connection failed" in response.json()["detail"]

    @patch("calorie_track_ai_bot.api.v1.goals.db_create_or_update_goal")
    def test_update_goal_table_not_found(self, mock_db_create_goal, client):
        """Test updating goal when table doesn't exist."""
        mock_db_create_goal.side_effect = Exception("Could not find the table")

        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 2500}
        response = client.patch("/goals", json=payload, headers=headers)

        assert response.status_code == 503
        assert "Goals feature not yet available" in response.json()["detail"]

    def test_invalid_goal_payload(self, client):
        """Test creating goal with invalid payload."""
        headers = {"x-user-id": "59357664"}
        payload = {"invalid_field": "invalid_value"}
        response = client.post("/goals", json=payload, headers=headers)

        assert response.status_code == 422  # Validation error

    def test_missing_daily_kcal_target(self, client):
        """Test creating goal without required daily_kcal_target field."""
        headers = {"x-user-id": "59357664"}
        payload = {}
        response = client.post("/goals", json=payload, headers=headers)

        assert response.status_code == 422  # Validation error

    def test_negative_daily_kcal_target(self, client):
        """Test creating goal with negative daily_kcal_target."""
        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": -100}
        response = client.post("/goals", json=payload, headers=headers)

        # Should return 500 because the database function will be called with negative value
        assert response.status_code == 500

    def test_zero_daily_kcal_target(self, client):
        """Test creating goal with zero daily_kcal_target."""
        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 0}
        response = client.post("/goals", json=payload, headers=headers)

        # Should return 500 because the database function will be called with zero value
        assert response.status_code == 500

    def test_very_large_daily_kcal_target(self, client):
        """Test creating goal with very large daily_kcal_target."""
        headers = {"x-user-id": "59357664"}
        payload = {"daily_kcal_target": 100000}
        response = client.post("/goals", json=payload, headers=headers)

        # Should return 500 because the database function will be called with large value
        assert response.status_code == 500

    def test_user_id_header_case_sensitivity(self, client):
        """Test that x-user-id header is case insensitive (FastAPI behavior)."""
        with patch("calorie_track_ai_bot.api.v1.goals.db_get_goal") as mock_db_get_goal:
            mock_db_get_goal.return_value = None

            # Test with different case - FastAPI treats headers as case-insensitive
            headers = {"X-User-ID": "59357664"}  # Different case
            response = client.get("/goals", headers=headers)

            assert response.status_code == 200
            # Should use the user ID since FastAPI is case-insensitive
            mock_db_get_goal.assert_called_once_with("59357664")

    def test_multiple_user_id_headers(self, client):
        """Test behavior with multiple x-user-id headers (HTTP spec behavior)."""
        with patch("calorie_track_ai_bot.api.v1.goals.db_get_goal") as mock_db_get_goal:
            mock_db_get_goal.return_value = None

            # HTTP headers with same name are concatenated with commas
            # FastAPI will use the first value
            headers = {"x-user-id": "59357664,99999999"}  # Comma-separated values
            response = client.get("/goals", headers=headers)

            assert response.status_code == 200
            # Should use the full comma-separated value
            mock_db_get_goal.assert_called_once_with("59357664,99999999")

    def test_user_id_with_whitespace(self, client):
        """Test user ID with leading/trailing whitespace."""
        with patch("calorie_track_ai_bot.api.v1.goals.db_get_goal") as mock_db_get_goal:
            mock_db_get_goal.return_value = None

            headers = {"x-user-id": "  59357664  "}  # With whitespace
            response = client.get("/goals", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is (including whitespace)
            mock_db_get_goal.assert_called_once_with("  59357664  ")

    def test_user_id_with_special_characters(self, client):
        """Test user ID with special characters."""
        with patch("calorie_track_ai_bot.api.v1.goals.db_get_goal") as mock_db_get_goal:
            mock_db_get_goal.return_value = None

            headers = {"x-user-id": "user@domain.com"}
            response = client.get("/goals", headers=headers)

            assert response.status_code == 200
            # Should use the user ID as-is
            mock_db_get_goal.assert_called_once_with("user@domain.com")
