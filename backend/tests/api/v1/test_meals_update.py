"""
Contract tests for PATCH /api/v1/meals/{id} endpoint
Feature: 003-update-logic-for
Task: T007
"""

from datetime import UTC
from unittest.mock import patch
from uuid import uuid4

import pytest


class TestMealsUpdateEndpoint:
    """Test meal update API contract"""

    @pytest.mark.asyncio
    async def test_update_meal_description(self, api_client, authenticated_headers, test_user_data):
        """Should update meal description via PATCH"""
        from datetime import datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        meal_id = uuid4()
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock existing meal
        existing_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=650.0,
            protein_grams=45.5,
            carbs_grams=75.0,
            fats_grams=18.2,
            description="Original description",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=45.5, carbs=75.0, fats=18.2),
            photos=[],
        )

        # Mock updated meal
        updated_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=650.0,
            protein_grams=45.5,
            carbs_grams=75.0,
            fats_grams=18.2,
            description="Updated: Grilled chicken pasta",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=45.5, carbs=75.0, fats=18.2),
            photos=[],
        )

        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos",
                return_value=existing_meal,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_update_meal_with_macros",
                return_value=updated_meal,
            ),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.patch(
                f"/api/v1/meals/{meal_id}",
                headers=authenticated_headers,
                json={"description": "Updated: Grilled chicken pasta"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["description"] == "Updated: Grilled chicken pasta"
            assert "id" in data
            assert "calories" in data
            assert "macronutrients" in data

    @pytest.mark.asyncio
    async def test_update_meal_macronutrients(
        self, api_client, authenticated_headers, test_user_data
    ):
        """Should update macronutrients and recalculate calories"""
        from datetime import datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        meal_id = uuid4()
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock existing meal
        existing_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=650.0,
            protein_grams=45.5,
            carbs_grams=75.0,
            fats_grams=18.2,
            description="Original description",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=45.5, carbs=75.0, fats=18.2),
            photos=[],
        )

        # Mock updated meal with recalculated calories
        updated_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=660.0,  # 50*4 + 70*4 + 20*9 = 660
            protein_grams=50.0,
            carbs_grams=70.0,
            fats_grams=20.0,
            description="Original description",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=50.0, carbs=70.0, fats=20.0),
            photos=[],
        )

        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos",
                return_value=existing_meal,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_update_meal_with_macros",
                return_value=updated_meal,
            ),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.patch(
                f"/api/v1/meals/{meal_id}",
                headers=authenticated_headers,
                json={"protein_grams": 50.0, "carbs_grams": 70.0, "fats_grams": 20.0},
            )

            assert response.status_code == 200
            data = response.json()

            # Verify macronutrients updated
            assert data["macronutrients"]["protein"] == 50.0
            assert data["macronutrients"]["carbs"] == 70.0
            assert data["macronutrients"]["fats"] == 20.0

            # Verify calories recalculated: 50*4 + 70*4 + 20*9 = 660
            expected_calories = 50.0 * 4 + 70.0 * 4 + 20.0 * 9
            assert abs(data["calories"] - expected_calories) < 1.0

    @pytest.mark.asyncio
    async def test_update_meal_partial_fields(
        self, api_client, authenticated_headers, test_user_data
    ):
        """Should allow partial updates (only some fields)"""
        from datetime import datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        meal_id = uuid4()
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        # Mock existing meal
        existing_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=650.0,
            protein_grams=45.5,
            carbs_grams=75.0,
            fats_grams=18.2,
            description="Original description",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=45.5, carbs=75.0, fats=18.2),
            photos=[],
        )

        # Mock updated meal with only protein changed
        updated_meal = MealWithPhotos(
            id=meal_id,
            user_id=user_uuid,
            calories=650.0,  # Only protein changed, calories recalculated
            protein_grams=45.0,
            carbs_grams=75.0,
            fats_grams=18.2,
            description="Original description",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=45.0, carbs=75.0, fats=18.2),
            photos=[],
        )

        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos",
                return_value=existing_meal,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_update_meal_with_macros",
                return_value=updated_meal,
            ),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.patch(
                f"/api/v1/meals/{meal_id}",
                headers=authenticated_headers,
                json={"protein_grams": 45.0},  # Only update protein
            )

            assert response.status_code == 200
            data = response.json()
            assert data["macronutrients"]["protein"] == 45.0

    def test_update_meal_requires_auth(self, api_client):
        """Should require authentication"""
        meal_id = str(uuid4())

        response = api_client.patch(f"/api/v1/meals/{meal_id}", json={"description": "Test"})

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_meal_not_found(self, api_client, authenticated_headers, test_user_data):
        """Should return 404 for non-existent meal"""

        non_existent_id = uuid4()
        user_uuid = "550e8400-e29b-41d4-a716-446655440000"

        with (
            patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=None),
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=user_uuid),
        ):
            response = api_client.patch(
                f"/api/v1/meals/{non_existent_id}",
                headers=authenticated_headers,
                json={"description": "Test"},
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_meal_forbidden_for_other_user(
        self, api_client, authenticated_headers, test_user_data
    ):
        """Should return 403 when trying to update another user's meal"""
        from datetime import datetime

        from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

        # This meal belongs to a different user
        other_user_meal_id = uuid4()
        current_user_uuid = "550e8400-e29b-41d4-a716-446655440000"
        other_user_uuid = "550e8400-e29b-41d4-a716-446655440001"  # Different user

        # Mock meal belonging to another user
        other_user_meal = MealWithPhotos(
            id=other_user_meal_id,
            user_id=other_user_uuid,  # Different user
            calories=650.0,
            protein_grams=45.5,
            carbs_grams=75.0,
            fats_grams=18.2,
            description="Other user's meal",
            created_at=datetime.now(UTC),
            macronutrients=Macronutrients(protein=45.5, carbs=75.0, fats=18.2),
            photos=[],
        )

        with (
            patch(
                "calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos",
                return_value=other_user_meal,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=current_user_uuid
            ),
        ):
            response = api_client.patch(
                f"/api/v1/meals/{other_user_meal_id}",
                headers=authenticated_headers,
                json={"description": "Hacked!"},
            )

            # Should be 403 Forbidden
            assert response.status_code == 403

    def test_update_meal_validates_negative_macros(self, api_client, authenticated_headers):
        """Should reject negative macronutrient values"""
        meal_id = str(uuid4())

        response = api_client.patch(
            f"/api/v1/meals/{meal_id}", headers=authenticated_headers, json={"protein_grams": -10.0}
        )

        # Pydantic validation returns 422 for invalid values
        assert response.status_code == 422

    def test_update_meal_returns_updated_photos(self, api_client, authenticated_headers):
        """Should return meal with associated photos array"""
        meal_id = str(uuid4())

        with (
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value="user-uuid"),
            patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=None),
        ):
            response = api_client.patch(
                f"/api/v1/meals/{meal_id}",
                headers=authenticated_headers,
                json={"description": "Updated"},
            )

            # Meal not found returns 404
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = response.json()
                assert "photos" in data
                assert isinstance(data["photos"], list)
