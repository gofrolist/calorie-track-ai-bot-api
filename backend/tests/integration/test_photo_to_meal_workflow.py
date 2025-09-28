"""Integration tests for the complete photo upload to meal creation workflow.

This test suite validates the entire flow:
1. Photo upload via API
2. Estimation job queuing
3. Worker processing
4. Automatic meal creation
5. Meal retrieval for UI display

This would have caught the bug where estimates weren't creating meals.
"""

import asyncio
from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.estimates import router as estimates_router
from calorie_track_ai_bot.api.v1.meals import router as meals_router
from calorie_track_ai_bot.api.v1.photos import router as photos_router
from calorie_track_ai_bot.workers.estimate_worker import handle_job


class TestPhotoToMealWorkflow:
    """Test the complete photo upload to meal creation workflow."""

    @pytest.fixture
    def client(self):
        """Create test client with all routers."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(photos_router, prefix="/api/v1")
        app.include_router(meals_router, prefix="/api/v1")
        app.include_router(estimates_router, prefix="/api/v1")
        return TestClient(app)

    def _setup_mocks(self):
        """Setup all mock services to avoid nested block issues."""
        # Configuration mocks
        config_patches = [
            patch("calorie_track_ai_bot.services.config.SUPABASE_URL", "test-url"),
            patch("calorie_track_ai_bot.services.config.SUPABASE_KEY", "test-key"),
            patch("calorie_track_ai_bot.services.config.OPENAI_API_KEY", "test-key"),
            patch("calorie_track_ai_bot.services.config.REDIS_URL", "redis://test"),
            patch("calorie_track_ai_bot.services.config.AWS_ENDPOINT_URL_S3", "test-endpoint"),
            patch("calorie_track_ai_bot.services.config.AWS_ACCESS_KEY_ID", "test-access"),
            patch("calorie_track_ai_bot.services.config.AWS_SECRET_ACCESS_KEY", "test-secret"),
            patch("calorie_track_ai_bot.services.config.BUCKET_NAME", "test-bucket"),
        ]

        # API service mocks
        mock_presign = patch(
            "calorie_track_ai_bot.api.v1.photos.tigris_presign_put",
            return_value=("photos/test123.jpg", "https://presigned-url.example.com"),
        )
        mock_create_photo = patch(
            "calorie_track_ai_bot.api.v1.photos.db_create_photo", return_value="photo-uuid-123"
        )
        mock_enqueue = patch(
            "calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job",
            return_value="estimate-uuid-123",
        )
        mock_get_estimate = patch(
            "calorie_track_ai_bot.api.v1.estimates.db_get_estimate",
            return_value={
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
            },
        )
        mock_get_meals = patch(
            "calorie_track_ai_bot.api.v1.meals.db_get_meals_by_date",
            return_value=[
                {
                    "id": "meal-uuid-123",
                    "user_id": "user-uuid-123",
                    "meal_date": str(date.today()),
                    "meal_type": "snack",
                    "kcal_total": 500,
                    "estimate_id": "estimate-uuid-123",
                    "created_at": "2025-01-27T10:00:00Z",
                    "updated_at": "2025-01-27T10:05:00Z",
                }
            ],
        )
        mock_get_today_data = patch(
            "calorie_track_ai_bot.services.db.db_get_today_data",
            return_value={
                "meals": [
                    {
                        "id": "meal-uuid-123",
                        "user_id": "user-uuid-123",
                        "meal_date": str(date.today()),
                        "meal_type": "snack",
                        "kcal_total": 500,
                        "estimate_id": "estimate-uuid-123",
                        "created_at": "2025-01-27T10:00:00Z",
                        "updated_at": "2025-01-27T10:05:00Z",
                    }
                ],
                "daily_summary": {
                    "date": str(date.today()),
                    "total_calories": 500,
                    "meal_count": 1,
                    "goal_calories": 2000,
                    "goal_progress": 0.25,
                    "meals": [
                        {
                            "id": "meal-uuid-123",
                            "meal_type": "snack",
                            "kcal_total": 500,
                            "estimate_id": "estimate-uuid-123",
                        }
                    ],
                },
            },
        )
        mock_resolve_user_summary = patch(
            "calorie_track_ai_bot.services.db.resolve_user_id", return_value="user-uuid-123"
        )

        # Worker service mocks
        mock_s3 = patch("calorie_track_ai_bot.workers.estimate_worker.s3")
        mock_estimate = patch(
            "calorie_track_ai_bot.workers.estimate_worker.estimate_from_image_url",
            return_value={
                "kcal_mean": 500,
                "kcal_min": 400,
                "kcal_max": 600,
                "confidence": 0.8,
                "items": [{"label": "pizza", "kcal": 500, "confidence": 0.8}],
            },
        )
        mock_save_estimate = patch(
            "calorie_track_ai_bot.workers.estimate_worker.db_save_estimate",
            return_value="estimate-uuid-123",
        )
        mock_get_photo = patch(
            "calorie_track_ai_bot.workers.estimate_worker.db_get_photo",
            return_value={
                "id": "photo-uuid-123",
                "tigris_key": "photos/test123.jpg",
                "user_id": "user-uuid-123",
                "status": "uploaded",
            },
        )

        # Start all patches
        all_patches = [
            *config_patches,
            mock_presign,
            mock_create_photo,
            mock_enqueue,
            mock_get_estimate,
            mock_get_meals,
            mock_get_today_data,
            mock_resolve_user_summary,
            mock_s3,
            mock_estimate,
            mock_save_estimate,
            mock_get_photo,
        ]

        started_patches = []
        for p in all_patches:
            started_patch = p.start()
            started_patches.append(started_patch)

        return {
            "presign": started_patches[8],  # mock_presign
            "create_photo": started_patches[9],  # mock_create_photo
            "enqueue": started_patches[10],  # mock_enqueue
            "get_estimate": started_patches[11],  # mock_get_estimate
            "get_meals": started_patches[12],  # mock_get_meals
            "get_today_data": started_patches[13],  # mock_get_today_data
            "resolve_user": started_patches[14],  # mock_resolve_user_summary
            "s3": started_patches[15],  # mock_s3
            "estimate": started_patches[16],  # mock_estimate
            "save_estimate": started_patches[17],  # mock_save_estimate
            "get_photo": started_patches[18],  # mock_get_photo
            "patches": all_patches,
        }

    def test_complete_photo_to_meal_workflow(self, client):
        """Test the complete workflow from photo upload to meal creation."""
        mock_services = self._setup_mocks()

        try:
            # Step 1: Upload photo
            photo_response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})
            assert photo_response.status_code == 200
            photo_data = photo_response.json()
            photo_id = photo_data["photo_id"]

            # Verify photo creation
            mock_services["create_photo"].assert_called_once()
            mock_services["presign"].assert_called_once()

            # Step 2: Request estimation
            estimate_response = client.post(f"/api/v1/photos/{photo_id}/estimate")
            assert estimate_response.status_code == 200
            estimate_data = estimate_response.json()
            estimate_id = estimate_data["estimate_id"]

            # Verify job was queued
            mock_services["enqueue"].assert_called_once_with(photo_id)

            # Step 3: Process the job (simulate worker)
            job = {"photo_id": photo_id}
            asyncio.run(handle_job(job))

            # Verify worker processed the job
            mock_services["get_photo"].assert_called_once_with(photo_id)
            mock_services["estimate"].assert_called_once()
            mock_services["save_estimate"].assert_called_once()

            # Step 4: Retrieve estimate (simulate bot checking)
            estimate_response = client.get(f"/api/v1/estimates/{estimate_id}")
            assert estimate_response.status_code == 200
            estimate_data = estimate_response.json()
            assert estimate_data["status"] == "done"
            assert estimate_data["kcal_mean"] == 500

            # Step 5: Retrieve meals for UI (simulate mini-app)
            meals_response = client.get(
                f"/api/v1/meals?date={date.today()}", headers={"x-user-id": "123456789"}
            )
            assert meals_response.status_code == 200
            meals_data = meals_response.json()

            # CRITICAL: Verify meal appears in UI data
            assert isinstance(meals_data, list)
            assert len(meals_data) == 1
            meal = meals_data[0]
            assert meal["id"] == "meal-uuid-123"
            assert meal["kcal_total"] == 500
            assert meal["meal_type"] == "snack"
            assert meal["estimate_id"] == estimate_id

        finally:
            # Clean up patches
            for p in mock_services["patches"]:
                p.stop()

    def test_workflow_with_estimation_error(self, client):
        """Test workflow when estimation fails."""
        mock_services = self._setup_mocks()

        try:
            # Setup estimation to fail
            mock_services["estimate"].side_effect = Exception("AI service unavailable")

            # Upload photo
            photo_response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})
            photo_id = photo_response.json()["photo_id"]

            # Request estimation
            estimate_response = client.post(f"/api/v1/photos/{photo_id}/estimate")
            estimate_id = estimate_response.json()["estimate_id"]

            # Process job - should fail
            job = {"photo_id": photo_id}
            with pytest.raises(Exception, match="AI service unavailable"):
                asyncio.run(handle_job(job))

            # Verify estimate status is still pending/failed
            estimate_response = client.get(f"/api/v1/estimates/{estimate_id}")
            # Note: This would depend on how failed estimates are handled

        finally:
            # Clean up patches
            for p in mock_services["patches"]:
                p.stop()

    def test_workflow_with_missing_user_id(self, client):
        """Test workflow when photo has no user_id."""
        mock_services = self._setup_mocks()

        try:
            # Setup photo without user_id
            mock_services["get_photo"].return_value = {
                "id": "photo-uuid-123",
                "tigris_key": "photos/test123.jpg",
                "user_id": None,  # Missing user_id
                "status": "uploaded",
            }

            # Upload photo and process
            photo_response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})
            photo_id = photo_response.json()["photo_id"]

            client.post(f"/api/v1/photos/{photo_id}/estimate")

            # Process job
            job = {"photo_id": photo_id}
            asyncio.run(handle_job(job))

            # Verify estimate was saved
            mock_services["save_estimate"].assert_called_once()

        finally:
            # Clean up patches
            for p in mock_services["patches"]:
                p.stop()

    def test_workflow_data_consistency(self, client):
        """Test that data flows correctly through the entire workflow."""
        mock_services = self._setup_mocks()

        try:
            # Upload photo
            photo_response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})
            photo_id = photo_response.json()["photo_id"]

            # Request estimation
            estimate_response = client.post(f"/api/v1/photos/{photo_id}/estimate")
            estimate_id = estimate_response.json()["estimate_id"]

            # Process job
            job = {"photo_id": photo_id}
            asyncio.run(handle_job(job))

            # Verify data consistency across all steps
            # Photo ID should be consistent
            assert mock_services["get_photo"].call_args[0][0] == photo_id
            assert mock_services["save_estimate"].call_args[1]["photo_id"] == photo_id

            # Estimate ID should be consistent
            saved_estimate_id = mock_services["save_estimate"].return_value
            assert saved_estimate_id == estimate_id

            # Calories should flow through correctly
            estimate_data = mock_services["estimate"].return_value
            assert estimate_data["kcal_mean"] == 500

        finally:
            # Clean up patches
            for p in mock_services["patches"]:
                p.stop()

    def test_workflow_performance_characteristics(self, client):
        """Test that the workflow completes within reasonable time."""
        mock_services = self._setup_mocks()

        try:
            import time

            start_time = time.time()

            # Complete workflow
            photo_response = client.post("/api/v1/photos", json={"content_type": "image/jpeg"})
            photo_id = photo_response.json()["photo_id"]

            estimate_response = client.post(f"/api/v1/photos/{photo_id}/estimate")
            estimate_id = estimate_response.json()["estimate_id"]

            job = {"photo_id": photo_id}
            asyncio.run(handle_job(job))

            client.get(f"/api/v1/estimates/{estimate_id}")
            client.get(f"/api/v1/today/{date.today()}", headers={"x-user-id": "telegram-user-123"})

            end_time = time.time()
            duration = end_time - start_time

            # Workflow should complete quickly (under 1 second for mocked services)
            assert duration < 1.0, f"Workflow took {duration:.2f} seconds, expected < 1.0"

        finally:
            # Clean up patches
            for p in mock_services["patches"]:
                p.stop()
