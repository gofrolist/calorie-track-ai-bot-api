"""Tests for estimates API endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.estimates import router


class TestEstimatesEndpoints:
    """Test estimate-related endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job")
    def test_estimate_photo_success(self, mock_enqueue, client):
        """Test successful photo estimation request."""
        mock_enqueue.return_value = "photo123"

        response = client.post("/photos/photo123/estimate")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "estimate_id" in data
        assert "status" in data

        # Check values
        assert data["estimate_id"] == "photo123"
        assert data["status"] == "queued"

    @patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job")
    def test_estimate_photo_different_ids(self, mock_enqueue, client):
        """Test photo estimation with different photo IDs."""
        test_cases = [
            "photo123",
            "photo456",
            "550e8400-e29b-41d4-a716-446655440000",
            "test-photo-789",
        ]

        for photo_id in test_cases:
            mock_enqueue.return_value = photo_id

            response = client.post(f"/photos/{photo_id}/estimate")

            assert response.status_code == 200
            data = response.json()
            assert data["estimate_id"] == photo_id
            assert data["status"] == "queued"

    @patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job")
    def test_estimate_photo_queue_error(self, mock_enqueue, client):
        """Test photo estimation when queue operation fails."""
        mock_enqueue.side_effect = Exception("Queue Error")

        response = client.post("/photos/photo123/estimate")

        # Should propagate the error
        assert response.status_code == 500

    def test_estimate_photo_methods(self, client):
        """Test that estimate photo only accepts POST requests."""
        get_response = client.get("/photos/photo123/estimate")
        assert get_response.status_code == 405  # Method Not Allowed

        put_response = client.put("/photos/photo123/estimate")
        assert put_response.status_code == 405

        delete_response = client.delete("/photos/photo123/estimate")
        assert delete_response.status_code == 405

    @patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate")
    def test_get_estimate_success(self, mock_db_get, client):
        """Test successful estimate retrieval."""
        estimate_data = {
            "id": "estimate123",
            "photo_id": "photo123",
            "kcal_mean": 500,
            "kcal_min": 400,
            "kcal_max": 600,
            "confidence": 0.8,
            "breakdown": [{"label": "pizza", "kcal": 500, "confidence": 0.8}],
            "status": "done",
        }
        mock_db_get.return_value = estimate_data

        response = client.get("/estimates/estimate123")

        assert response.status_code == 200
        data = response.json()
        assert data == estimate_data

    @patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate")
    def test_get_estimate_not_found(self, mock_db_get, client):
        """Test estimate retrieval when estimate doesn't exist."""
        mock_db_get.return_value = None

        response = client.get("/estimates/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Not found"

    @patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate")
    def test_get_estimate_db_error(self, mock_db_get, client):
        """Test estimate retrieval when database operation fails."""
        mock_db_get.side_effect = Exception("Database Error")

        response = client.get("/estimates/estimate123")

        # Should propagate the error
        assert response.status_code == 500

    def test_get_estimate_methods(self, client):
        """Test that get estimate only accepts GET requests."""
        post_response = client.post("/estimates/estimate123")
        assert post_response.status_code == 405  # Method Not Allowed

        put_response = client.put("/estimates/estimate123")
        assert put_response.status_code == 405

        delete_response = client.delete("/estimates/estimate123")
        assert delete_response.status_code == 405

    @patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate")
    def test_get_estimate_different_ids(self, mock_db_get, client):
        """Test estimate retrieval with different estimate IDs."""
        test_cases = [
            "estimate123",
            "estimate456",
            "550e8400-e29b-41d4-a716-446655440000",
            "test-estimate-789",
        ]

        for estimate_id in test_cases:
            estimate_data = {
                "id": estimate_id,
                "photo_id": "photo123",
                "kcal_mean": 300,
                "kcal_min": 250,
                "kcal_max": 350,
                "confidence": 0.7,
                "breakdown": [],
                "status": "done",
            }
            mock_db_get.return_value = estimate_data

            response = client.get(f"/estimates/{estimate_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == estimate_id

    def test_estimate_endpoints_content_type(self, client):
        """Test that estimate endpoints return JSON content type."""
        with (
            patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job") as mock_enqueue,
            patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate") as mock_db_get,
        ):
            mock_enqueue.return_value = "photo123"

            mock_db_get.return_value = {
                "id": "estimate123",
                "photo_id": "photo123",
                "kcal_mean": 300,
                "kcal_min": 250,
                "kcal_max": 350,
                "confidence": 0.7,
                "breakdown": [],
                "status": "done",
            }

            # Test POST endpoint
            post_response = client.post("/photos/photo123/estimate")
            assert post_response.headers["content-type"] == "application/json"

            # Test GET endpoint
            get_response = client.get("/estimates/estimate123")
            assert get_response.headers["content-type"] == "application/json"

    @patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job")
    def test_estimate_photo_response_structure(self, mock_enqueue, client):
        """Test that estimate photo returns consistent response structure."""
        mock_enqueue.return_value = "photo123"

        response = client.post("/photos/photo123/estimate")
        data = response.json()

        # Should be valid JSON
        assert isinstance(data, dict)

        # Should have required fields
        assert "estimate_id" in data
        assert "status" in data

        # Values should be strings
        assert isinstance(data["estimate_id"], str)
        assert isinstance(data["status"], str)

        # Status should be "queued"
        assert data["status"] == "queued"
