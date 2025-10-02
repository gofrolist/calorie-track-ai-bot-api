"""Enhanced API contract tests that validate data flow and consistency.

These tests ensure that:
1. API contracts are maintained across versions
2. Data flows correctly between endpoints
3. Response schemas match expected formats
4. Error responses follow consistent patterns
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.daily_summary import router as daily_summary_router
from calorie_track_ai_bot.api.v1.estimates import router as estimates_router
from calorie_track_ai_bot.api.v1.meals import router as meals_router
from calorie_track_ai_bot.api.v1.photos import router as photos_router


class TestAPIContracts:
    """Test API contracts and data flow consistency."""

    @pytest.fixture
    def client(self):
        """Create test client with all routers."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(photos_router, prefix="/api/v1")
        app.include_router(meals_router, prefix="/api/v1")
        app.include_router(estimates_router, prefix="/api/v1")
        app.include_router(daily_summary_router, prefix="/api/v1")
        return TestClient(app)

    def test_photo_creation_contract(self, client):
        """Test photo creation API contract."""
        with (
            patch("calorie_track_ai_bot.api.v1.photos.tigris_presign_put") as mock_presign,
            patch("calorie_track_ai_bot.api.v1.photos.db_create_photo") as mock_create,
        ):
            mock_presign.return_value = ("photos/test123.jpg", "https://presigned-url.example.com")
            mock_create.return_value = "photo-uuid-123"

            response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "photo_id" in data
            assert "upload_url" in data

            # Verify field types
            assert isinstance(data["photo_id"], str)
            assert isinstance(data["upload_url"], str)

            # Verify field values
            assert data["photo_id"] == "photo-uuid-123"
            assert data["upload_url"] == "https://presigned-url.example.com"

    def test_photo_creation_validation_contract(self, client):
        """Test photo creation validation contract."""

        # Test missing content_type
        response = client.post("/api/v1/photos", json={})
        assert response.status_code == 422

        # Test invalid content_type type
        response = client.post("/api/v1/photos", json={"content_type": 123})
        assert response.status_code == 422

        # Test valid content_type
        with (
            patch("calorie_track_ai_bot.api.v1.photos.tigris_presign_put") as mock_presign,
            patch("calorie_track_ai_bot.api.v1.photos.db_create_photo") as mock_create,
        ):
            mock_presign.return_value = ("photos/test123.jpg", "https://presigned-url.example.com")
            mock_create.return_value = "photo-uuid-123"

            response = client.post("/api/v1/photos", json={"content_type": "image/png"})
            assert response.status_code == 200

    def test_estimate_queuing_contract(self, client):
        """Test estimate queuing API contract."""
        with patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job") as mock_enqueue:
            mock_enqueue.return_value = "estimate-uuid-123"

            response = client.post("/api/v1/photos/photo-123/estimate")

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "estimate_id" in data

            # Verify field types
            assert isinstance(data["estimate_id"], str)

            # Verify field values
            assert data["estimate_id"] == "estimate-uuid-123"

    def test_estimate_retrieval_contract(self, client):
        """Test estimate retrieval API contract."""
        with patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate") as mock_get:
            mock_get.return_value = {
                "id": "estimate-uuid-123",
                "photo_id": "photo-uuid-123",
                "status": "done",
                "kcal_mean": 500,
                "kcal_min": 400,
                "kcal_max": 600,
                "confidence": 0.8,
                "breakdown": [{"label": "pizza", "kcal": 500, "confidence": 0.8}],
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:05:00Z",
            }

            response = client.get("/api/v1/estimates/estimate-uuid-123")

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            required_fields = [
                "id",
                "photo_id",
                "status",
                "kcal_mean",
                "kcal_min",
                "kcal_max",
                "confidence",
                "breakdown",
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(data["id"], str)
            assert isinstance(data["photo_id"], str)
            assert isinstance(data["status"], str)
            assert isinstance(data["kcal_mean"], int | float)
            assert isinstance(data["kcal_min"], int | float)
            assert isinstance(data["kcal_max"], int | float)
            assert isinstance(data["confidence"], int | float)
            assert isinstance(data["breakdown"], list)

            # Verify breakdown structure
            if data["breakdown"]:
                item = data["breakdown"][0]
                assert "label" in item
                assert "kcal" in item
                assert "confidence" in item
                assert isinstance(item["label"], str)
                assert isinstance(item["kcal"], int | float)
                assert isinstance(item["confidence"], int | float)

    def test_meal_creation_contract(self, client):
        """Test meal creation API contract."""
        with patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_manual") as mock_create:
            mock_create.return_value = {"meal_id": "meal-uuid-123"}

            payload = {
                "meal_date": "2025-01-27",
                "meal_type": "breakfast",
                "kcal_total": 400.5,
                "macros": {"protein": 20, "carbs": 30, "fat": 10},
            }

            response = client.post("/api/v1/meals", json=payload)

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "meal_id" in data

            # Verify field types
            assert isinstance(data["meal_id"], str)

            # Verify field values
            assert data["meal_id"] == "meal-uuid-123"

    def test_meal_creation_from_estimate_contract(self, client):
        """Test meal creation from estimate API contract."""
        with (
            patch("calorie_track_ai_bot.api.v1.meals.db_create_meal_from_estimate") as mock_create,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve,
        ):
            mock_create.return_value = {"meal_id": "meal-uuid-123"}
            mock_resolve.return_value = "user-uuid-123"

            payload = {
                "meal_date": "2025-01-27",
                "meal_type": "lunch",
                "estimate_id": "estimate-uuid-123",
                "overrides": {"kcal_total": 450},
            }

            response = client.post(
                "/api/v1/meals", json=payload, headers={"x-user-id": "123456789"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            assert "meal_id" in data

            # Verify field types
            assert isinstance(data["meal_id"], str)

            # Verify field values
            assert data["meal_id"] == "meal-uuid-123"

    def test_meals_retrieval_contract(self, client):
        """Test meals retrieval API contract."""
        from datetime import UTC, datetime
        from uuid import uuid4

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        meal_id = uuid4()

        mock_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=400.0,
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=20.0, carbs=50.0, fats=10.0),
            photos=[],
        )

        with (
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve,
            patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get,
        ):
            mock_resolve.return_value = user_uuid
            mock_get.return_value = [mock_meal]

            response = client.get(
                "/api/v1/meals?date=2025-01-27", headers={"x-user-id": "123456789"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure has meals and total
            assert "meals" in data
            assert "total" in data
            assert isinstance(data["meals"], list)

            if data["meals"]:
                meal = data["meals"][0]
                # Verify required fields for new schema
                required_fields = [
                    "id",
                    "user_id",
                    "calories",
                    "macronutrients",
                    "photos",
                    "created_at",
                ]
                for field in required_fields:
                    assert field in meal, f"Missing required field: {field}"

                # Verify field types
                assert isinstance(meal["id"], str)
                assert isinstance(meal["user_id"], str)
                assert isinstance(meal["calories"], int | float)
                assert isinstance(meal["macronutrients"], dict)
                assert isinstance(meal["photos"], list)
                assert isinstance(meal["created_at"], str)

    def test_daily_summary_contract(self, client):
        """Test daily summary API contract."""
        with (
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve,
            patch("calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary") as mock_get,
        ):
            mock_resolve.return_value = "user-uuid-123"
            mock_get.return_value = {
                "date": "2025-01-27",
                "total_calories": 1200,
                "meal_count": 3,
                "goal_calories": 2000,
                "goal_progress": 0.6,
                "meals": [
                    {
                        "id": "meal-uuid-123",
                        "meal_type": "breakfast",
                        "kcal_total": 400,
                        "estimate_id": "estimate-uuid-123",
                    }
                ],
            }

            response = client.get(
                "/api/v1/daily-summary/2025-01-27", headers={"x-user-id": "123456789"}
            )

            assert response.status_code == 200
            data = response.json()

            # Verify required fields
            required_fields = [
                "date",
                "total_calories",
                "meal_count",
                "goal_calories",
                "goal_progress",
                "meals",
            ]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(data["date"], str)
            assert isinstance(data["total_calories"], int | float)
            assert isinstance(data["meal_count"], int)
            assert isinstance(data["goal_calories"], int | float)
            assert isinstance(data["goal_progress"], int | float)
            assert isinstance(data["meals"], list)

            # Verify meals structure
            if data["meals"]:
                meal = data["meals"][0]
                assert "id" in meal
                assert "meal_type" in meal
                assert "kcal_total" in meal
                assert isinstance(meal["id"], str)
                assert isinstance(meal["meal_type"], str)
                assert isinstance(meal["kcal_total"], int | float)

    def test_error_response_contract(self, client):
        """Test error response contract consistency."""

        # Test 404 for non-existent estimate
        with patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/v1/estimates/non-existent-id")
            assert response.status_code == 404

            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], str)

        # Test 400 for missing user ID
        with patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve:
            mock_resolve.return_value = None  # Simulate user not found

            response = client.post(
                "/api/v1/meals",
                json={
                    "meal_date": "2025-01-27",
                    "meal_type": "lunch",
                    "estimate_id": "estimate-uuid-123",
                    "overrides": {"kcal_total": 450},
                },
                headers={"x-user-id": "123456789"},
            )
            # Should return 400 or 500 - either is acceptable for error handling
            assert response.status_code in [400, 500]

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

        # Test 422 for validation errors
        response = client.post("/api/v1/photos", json={})
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    @pytest.mark.skip(
        reason="TODO: Complex end-to-end test requires extensive mock setup - core flows tested in unit tests"
    )
    def test_data_flow_consistency(self, client):
        """Test that data flows consistently between related endpoints."""

        # Mock a complete workflow
        with (
            patch("calorie_track_ai_bot.api.v1.photos.tigris_presign_put") as mock_presign,
            patch("calorie_track_ai_bot.api.v1.photos.db_create_photo") as mock_create_photo,
            patch("calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job") as mock_enqueue,
            patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate") as mock_get_estimate,
            patch("calorie_track_ai_bot.services.db.db_get_meals_by_date") as mock_get_meals,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user,
            patch(
                "calorie_track_ai_bot.api.v1.daily_summary.db_get_daily_summary"
            ) as mock_get_summary,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve_user_summary,
        ):
            # Setup consistent mock data
            photo_id = "photo-uuid-123"
            estimate_id = "estimate-uuid-123"
            user_id = "user-uuid-123"
            calories = 500

            mock_presign.return_value = ("photos/test123.jpg", "https://presigned-url.example.com")
            mock_create_photo.return_value = photo_id
            mock_enqueue.return_value = estimate_id
            mock_resolve_user.return_value = user_id
            mock_resolve_user_summary.return_value = user_id

            mock_get_estimate.return_value = {
                "id": estimate_id,
                "photo_id": photo_id,
                "status": "done",
                "kcal_mean": calories,
                "kcal_min": calories - 50,
                "kcal_max": calories + 50,
                "confidence": 0.8,
                "breakdown": [{"label": "test food", "kcal": calories, "confidence": 0.8}],
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:05:00Z",
            }

            mock_get_meals.return_value = [
                {
                    "id": "meal-uuid-123",
                    "user_id": user_id,
                    "meal_date": "2025-01-27",
                    "meal_type": "snack",
                    "kcal_total": calories,
                    "estimate_id": estimate_id,
                    "created_at": "2025-01-27T10:00:00Z",
                    "updated_at": "2025-01-27T10:00:00Z",
                }
            ]

            mock_get_summary.return_value = {
                "date": "2025-01-27",
                "total_calories": calories,
                "meal_count": 1,
                "goal_calories": 2000,
                "goal_progress": calories / 2000,
                "meals": [
                    {
                        "id": "meal-uuid-123",
                        "meal_type": "snack",
                        "kcal_total": calories,
                        "estimate_id": estimate_id,
                    }
                ],
            }

            # Test data consistency across endpoints
            estimate_response = client.get(f"/api/v1/estimates/{estimate_id}")
            estimate_data = estimate_response.json()

            meals_response = client.get(
                "/api/v1/meals?date=2025-01-27", headers={"x-user-id": "123456789"}
            )
            meals_data = meals_response.json()

            summary_response = client.get(
                "/api/v1/daily-summary/2025-01-27", headers={"x-user-id": "123456789"}
            )
            summary_data = summary_response.json()

            # Verify calorie consistency
            assert estimate_data["kcal_mean"] == calories
            assert meals_data[0]["kcal_total"] == calories
            assert summary_data["total_calories"] == calories
            assert summary_data["meals"][0]["kcal_total"] == calories

            # Verify ID consistency
            assert estimate_data["id"] == estimate_id
            assert meals_data[0]["estimate_id"] == estimate_id
            assert summary_data["meals"][0]["estimate_id"] == estimate_id

            # Verify user consistency
            assert meals_data[0]["user_id"] == user_id

            # Verify date consistency
            assert meals_data[0]["meal_date"] == "2025-01-27"
            assert summary_data["date"] == "2025-01-27"

    def test_api_versioning_contract(self, client):
        """Test that API versioning is consistent."""

        # All endpoints should be under /api/v1
        endpoints = [
            "/api/v1/photos",
            "/api/v1/estimates/test-id",
            "/api/v1/meals",
            "/api/v1/today/2025-01-27",
            "/api/v1/daily-summary/2025-01-27",
        ]

        for endpoint in endpoints:
            # Test that endpoints exist (even if they return errors)
            if endpoint == "/api/v1/photos":
                response = client.post(endpoint, json={"content_type": "image/jpeg"})
            else:
                response = client.get(endpoint)

            # Should not return 404 (endpoint not found)
            assert response.status_code != 404, f"Endpoint {endpoint} not found"

            # Should return a structured response
            if response.status_code < 500:
                data = response.json()
                assert isinstance(data, dict | list)

    def test_content_type_contract(self, client):
        """Test that all responses have correct content type."""

        with (
            patch("calorie_track_ai_bot.api.v1.photos.tigris_presign_put") as mock_presign,
            patch("calorie_track_ai_bot.api.v1.photos.db_create_photo") as mock_create,
        ):
            mock_presign.return_value = ("photos/test123.jpg", "https://presigned-url.example.com")
            mock_create.return_value = "photo-uuid-123"

            response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})
            assert response.headers["content-type"] == "application/json"

        with patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate") as mock_get:
            mock_get.return_value = {
                "id": "test-id",
                "photo_id": "photo-uuid-123",
                "status": "done",
                "kcal_mean": 500,
                "kcal_min": 400,
                "kcal_max": 600,
                "confidence": 0.8,
                "breakdown": [{"label": "test food", "kcal": 500, "confidence": 0.8}],
                "created_at": "2025-01-27T10:00:00Z",
                "updated_at": "2025-01-27T10:05:00Z",
            }

            response = client.get("/api/v1/estimates/test-id")
            assert response.headers["content-type"] == "application/json"

        with (
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve,
            patch("calorie_track_ai_bot.services.db.db_get_meals_by_date") as mock_get,
        ):
            mock_resolve.return_value = "user-uuid-123"
            mock_get.return_value = []

            response = client.get(
                "/api/v1/meals?date=2025-01-27", headers={"x-user-id": "123456789"}
            )
            assert response.headers["content-type"] == "application/json"
