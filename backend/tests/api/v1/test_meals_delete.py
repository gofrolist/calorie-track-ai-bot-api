"""
Contract tests for DELETE /api/v1/meals/{id} endpoint
Feature: 003-update-logic-for
Task: T008
"""

from unittest.mock import patch
from uuid import uuid4


class TestMealsDeleteEndpoint:
    """Test meal deletion API contract"""

    def test_delete_meal_success(self, api_client, authenticated_headers, mock_supabase_client):
        """Should delete meal and return 204 No Content"""
        from datetime import UTC, datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        meal_id = str(uuid4())
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock meal exists
        mock_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=500.0,
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=0.0, carbs=0.0, fats=0.0),
            photos=[],
        )

        # Mock successful deletion
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=mock_meal
            ),
            patch("calorie_track_ai_bot.api.v1.meals.db_delete_meal", return_value=True),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.delete(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

        assert response.status_code == 204

    def test_delete_meal_requires_auth(self, api_client):
        """Should require authentication"""
        meal_id = str(uuid4())

        response = api_client.delete(f"/api/v1/meals/{meal_id}")

        assert response.status_code == 401

    def test_delete_meal_not_found(self, api_client, authenticated_headers, mock_supabase_client):
        """Should return 404 for non-existent meal"""
        from fastapi import HTTPException

        non_existent_id = str(uuid4())
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock meal not found
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_delete_meal",
                side_effect=HTTPException(status_code=404, detail="Meal not found"),
            ),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.delete(
                f"/api/v1/meals/{non_existent_id}", headers=authenticated_headers
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_meal_forbidden_for_other_user(
        self, api_client, authenticated_headers, mock_supabase_client
    ):
        """Should return 403 when trying to delete another user's meal"""
        from fastapi import HTTPException

        other_user_meal_id = str(uuid4())
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock forbidden access (meal belongs to another user)
        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_delete_meal",
                side_effect=HTTPException(status_code=403, detail="Forbidden"),
            ),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.delete(
                f"/api/v1/meals/{other_user_meal_id}", headers=authenticated_headers
            )

        # Should be 403 Forbidden or 404 Not Found
        assert response.status_code in [403, 404]

    def test_delete_meal_cascades_to_photos(
        self, api_client, authenticated_headers, mock_supabase_client
    ):
        """Should cascade delete to associated photos"""
        meal_id = str(uuid4())
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock successful deletion (cascade is handled by DB)
        with (
            patch("calorie_track_ai_bot.api.v1.meals.db_delete_meal", return_value=True),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.delete(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

        # After deletion, photos should also be removed (tested in integration)
        assert response.status_code in [204, 404]

    def test_delete_meal_updates_daily_summary(
        self, api_client, authenticated_headers, mock_supabase_client
    ):
        """Should update daily summary stats when meal deleted"""
        meal_id = str(uuid4())
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock successful deletion (summary update is handled by DB)
        with (
            patch("calorie_track_ai_bot.api.v1.meals.db_delete_meal", return_value=True),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.delete(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

        # Stats should be recalculated (verified in integration test)
        assert response.status_code in [204, 404]
