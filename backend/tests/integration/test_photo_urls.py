"""
Integration tests for photo URL generation and display functionality.
Tests the backend photo URL generation and meal data enhancement.
"""

from datetime import date
from unittest.mock import AsyncMock, Mock, patch

import pytest

from calorie_track_ai_bot.schemas import MealCreateFromEstimateRequest, MealType
from calorie_track_ai_bot.services.db import (
    _enhance_meal_with_related_data,
    db_create_meal_from_estimate,
    db_get_meal,
    db_get_meals_by_date,
)


class TestPhotoUrlGeneration:
    """Test photo URL generation in database operations."""

    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client for photo URL generation."""
        mock_s3 = Mock()
        mock_s3.generate_presigned_url = Mock(return_value="https://presigned-url.example.com")
        return mock_s3

    @pytest.fixture
    def mock_db_operations(self):
        """Mock database operations for testing."""
        with (
            patch("calorie_track_ai_bot.services.db.sb") as mock_db,
            patch("calorie_track_ai_bot.services.db.resolve_user_id") as mock_resolve,
            patch(
                "calorie_track_ai_bot.services.db.db_get_estimate", new_callable=AsyncMock
            ) as mock_get_estimate,
            patch(
                "calorie_track_ai_bot.services.db.db_get_photo", new_callable=AsyncMock
            ) as mock_get_photo,
            patch("calorie_track_ai_bot.services.db.s3") as mock_s3,
        ):
            # Setup mock database responses
            mock_meal_data = {
                "id": "meal-uuid-123",
                "user_id": "user-uuid-123",
                "meal_date": "2025-01-27",
                "meal_type": "snack",
                "kcal_total": 650,
                "estimate_id": "estimate-uuid-123",
                "created_at": "2025-01-27T10:00:00Z",
            }

            # Mock for db_get_meal (single result)
            def mock_get_meal_result():
                response = Mock()
                response.data = [mock_meal_data]
                return response

            # Mock for db_get_meals_by_date (list result)
            def mock_get_meals_result():
                response = Mock()
                response.data = [mock_meal_data]
                return response

            # Setup the chain of mocks for Supabase queries
            table_mock = Mock()
            select_mock = Mock()
            eq_mock_1 = Mock()
            eq_mock_2 = Mock()

            table_mock.select.return_value = select_mock
            select_mock.eq.return_value = eq_mock_1
            eq_mock_1.eq.return_value = eq_mock_2
            eq_mock_2.execute.return_value = mock_get_meals_result()

            # For single meal query (no second eq)
            eq_mock_1.execute.return_value = mock_get_meal_result()

            mock_db.table.return_value = table_mock

            mock_resolve.return_value = "user-uuid-123"
            mock_get_estimate.return_value = {
                "id": "estimate-uuid-123",
                "photo_id": "photo-uuid-123",
                "kcal_mean": 650,
                "breakdown": [{"label": "chicken breast", "kcal": 300}],
            }
            mock_get_photo.return_value = {
                "id": "photo-uuid-123",
                "tigris_key": "photos/test123.jpg",
                "user_id": "user-uuid-123",
                "status": "uploaded",
            }
            mock_s3.generate_presigned_url.return_value = "https://photos.example.com/test123.jpg"

            yield {
                "db": mock_db,
                "resolve": mock_resolve,
                "get_estimate": mock_get_estimate,
                "get_photo": mock_get_photo,
                "s3": mock_s3,
            }

    @pytest.mark.asyncio
    async def test_enhance_meal_with_photo_url(self, mock_db_operations):
        """Test that _enhance_meal_with_related_data adds photo_url to meals."""
        meal_data = {
            "id": "meal-uuid-123",
            "estimate_id": "estimate-uuid-123",
            "kcal_total": 650,
            "created_at": "2025-01-27T10:00:00Z",
        }

        await _enhance_meal_with_related_data(meal_data)

        assert "photo_url" in meal_data
        assert meal_data["photo_url"] == "https://photos.example.com/test123.jpg"
        assert "macros" in meal_data
        assert meal_data["macros"] == {"protein_g": 0, "fat_g": 0, "carbs_g": 0}
        assert "corrected" in meal_data
        assert meal_data["corrected"] is False
        assert "updated_at" in meal_data

    @pytest.mark.asyncio
    async def test_enhance_meal_without_estimate(self, mock_db_operations):
        """Test meal enhancement when no estimate exists."""
        meal_data = {
            "id": "meal-uuid-123",
            "kcal_total": 500,
            "created_at": "2025-01-27T10:00:00Z",
            # No estimate_id
        }

        await _enhance_meal_with_related_data(meal_data)

        assert meal_data.get("photo_url") is None
        assert meal_data["macros"] == {"protein_g": 0, "fat_g": 0, "carbs_g": 0}
        assert meal_data["corrected"] is False
        assert "updated_at" in meal_data

    @pytest.mark.asyncio
    async def test_enhance_meal_without_updated_at(self, mock_db_operations):
        """Test meal enhancement when updated_at is missing."""
        meal_data = {
            "id": "meal-uuid-123",
            "estimate_id": "estimate-uuid-123",
            "kcal_total": 650,
            "created_at": "2025-01-27T10:00:00Z",
            # No updated_at
        }

        await _enhance_meal_with_related_data(meal_data)

        assert meal_data["updated_at"] == meal_data["created_at"]

    @pytest.mark.asyncio
    async def test_enhance_meal_missing_timestamps(self, mock_db_operations):
        """Test meal enhancement when both timestamps are missing."""
        meal_data = {
            "id": "meal-uuid-123",
            "estimate_id": "estimate-uuid-123",
            "kcal_total": 650,
            # No timestamps
        }

        await _enhance_meal_with_related_data(meal_data)

        assert "created_at" in meal_data
        assert "updated_at" in meal_data
        # Both should be recent timestamps
        assert meal_data["created_at"] == meal_data["updated_at"]

    @pytest.mark.asyncio
    async def test_photo_url_generation_error_handling(self, mock_db_operations):
        """Test error handling when photo URL generation fails."""
        # Make S3 URL generation fail
        mock_db_operations["s3"].generate_presigned_url.side_effect = Exception("S3 Error")

        meal_data = {
            "id": "meal-uuid-123",
            "estimate_id": "estimate-uuid-123",
            "kcal_total": 650,
            "created_at": "2025-01-27T10:00:00Z",
        }

        await _enhance_meal_with_related_data(meal_data)

        # Should gracefully handle the error and set photo_url to None
        assert meal_data["photo_url"] is None
        # Other fields should still be populated
        assert "macros" in meal_data
        assert "corrected" in meal_data

    @pytest.mark.asyncio
    async def test_get_meal_includes_photo_url(self, mock_db_operations):
        """Test that db_get_meal returns meals with photo URLs."""
        meal = await db_get_meal("meal-uuid-123")

        assert meal is not None
        assert "photo_url" in meal
        assert meal["photo_url"] == "https://photos.example.com/test123.jpg"
        assert "macros" in meal
        assert "corrected" in meal

    @pytest.mark.asyncio
    async def test_get_meals_by_date_includes_photo_urls(self, mock_db_operations):
        """Test that db_get_meals_by_date returns meals with photo URLs."""
        meals = await db_get_meals_by_date("2025-01-27", "telegram-user-123")

        assert len(meals) == 1
        meal = meals[0]
        assert "photo_url" in meal
        assert meal["photo_url"] == "https://photos.example.com/test123.jpg"
        assert "macros" in meal
        assert "corrected" in meal

    @pytest.mark.asyncio
    async def test_create_meal_from_estimate_with_kcal_from_estimate(self):
        """Test that meals created from estimates get kcal_total from estimate.kcal_mean."""
        with (
            patch("calorie_track_ai_bot.services.db.sb") as mock_db,
            patch(
                "calorie_track_ai_bot.services.db.db_get_estimate", new_callable=AsyncMock
            ) as mock_get_estimate,
        ):
            mock_db.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_get_estimate.return_value = {
                "id": "estimate-uuid-123",
                "kcal_mean": 850,  # This should be used as kcal_total
                "breakdown": [{"label": "test food", "kcal": 850}],
            }

            meal_request = MealCreateFromEstimateRequest(
                estimate_id="estimate-uuid-123",
                meal_date=date.today(),
                meal_type=MealType.snack,
            )

            await db_create_meal_from_estimate(meal_request, "telegram-user-123")

            # Verify the meal was created with kcal_total from estimate
            mock_db.table.return_value.insert.assert_called_once()
            call_args = mock_db.table.return_value.insert.call_args[0][0]

            # The inserted meal should have kcal_total = 850 from the estimate
            assert call_args["kcal_total"] == 850
            assert call_args["estimate_id"] == "estimate-uuid-123"
            assert call_args["meal_type"] == "snack"

    @pytest.mark.asyncio
    async def test_create_meal_from_estimate_with_kcal_override(self):
        """Test that meal kcal can be overridden when creating from estimate."""
        with (
            patch("calorie_track_ai_bot.services.db.sb") as mock_db,
            patch(
                "calorie_track_ai_bot.services.db.db_get_estimate", new_callable=AsyncMock
            ) as mock_get_estimate,
        ):
            mock_db.table.return_value.insert.return_value.execute.return_value = Mock()
            mock_get_estimate.return_value = {
                "id": "estimate-uuid-123",
                "kcal_mean": 850,  # This should be overridden
                "breakdown": [{"label": "test food", "kcal": 850}],
            }

            meal_request = MealCreateFromEstimateRequest(
                estimate_id="estimate-uuid-123",
                meal_date=date.today(),
                meal_type=MealType.snack,
                overrides={"kcal_total": 750},  # Override to 750
            )

            await db_create_meal_from_estimate(meal_request, "telegram-user-123")

            # Verify the meal was created with overridden kcal_total
            mock_db.table.return_value.insert.assert_called_once()
            call_args = mock_db.table.return_value.insert.call_args[0][0]

            # The inserted meal should have kcal_total = 750 (overridden)
            assert call_args["kcal_total"] == 750
            assert call_args["estimate_id"] == "estimate-uuid-123"
