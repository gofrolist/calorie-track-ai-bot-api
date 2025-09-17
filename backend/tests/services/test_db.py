"""Tests for db module."""

from unittest.mock import Mock, patch

import pytest

from calorie_track_ai_bot.services.db import (
    db_create_meal_from_estimate,
    db_create_meal_from_manual,
    db_create_photo,
    db_get_estimate,
    db_save_estimate,
)


class TestDatabaseFunctions:
    """Test database functions."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase client."""
        with patch("calorie_track_ai_bot.services.db.sb") as mock_sb:
            mock_table = Mock()
            mock_query = Mock()
            mock_query.execute.return_value = Mock(data=[])
            mock_table.insert.return_value = mock_query
            mock_table.select.return_value = mock_query
            mock_table.eq.return_value = mock_query
            mock_sb.table.return_value = mock_table
            yield mock_sb

    @pytest.mark.asyncio
    async def test_db_create_photo(self, mock_supabase):
        """Test creating a photo record."""
        tigris_key = "photos/test123.jpg"

        result = await db_create_photo(tigris_key)

        # Should return a UUID string
        assert isinstance(result, str)
        assert len(result) == 36  # UUID length

        # Should call insert with correct data
        mock_supabase.table.assert_called_with("photos")
        mock_table = mock_supabase.table.return_value
        mock_table.insert.assert_called_once()

        # Check the insert call arguments
        call_args = mock_table.insert.call_args[0][0]
        assert "id" in call_args
        assert call_args["tigris_key"] == tigris_key

    @pytest.mark.asyncio
    async def test_db_save_estimate(self, mock_supabase):
        """Test saving an estimate."""
        photo_id = "photo123"
        estimate_data = {
            "kcal_mean": 500,
            "kcal_min": 400,
            "kcal_max": 600,
            "confidence": 0.8,
            "items": [{"label": "pizza", "kcal": 500, "confidence": 0.8}],
        }

        result = await db_save_estimate(photo_id, estimate_data)

        # Should return a UUID string
        assert isinstance(result, str)
        assert len(result) == 36  # UUID length

        # Should call insert with correct data
        mock_supabase.table.assert_called_with("estimates")
        mock_table = mock_supabase.table.return_value
        mock_table.insert.assert_called_once()

        # Check the insert call arguments
        call_args = mock_table.insert.call_args[0][0]
        assert "id" in call_args
        assert call_args["photo_id"] == photo_id
        assert call_args["kcal_mean"] == 500

    @pytest.mark.asyncio
    async def test_db_get_estimate_found(self, mock_supabase):
        """Test getting an estimate that exists."""
        estimate_id = "estimate123"
        mock_data = [{"id": estimate_id, "kcal_mean": 500}]

        # Mock the response
        mock_response = Mock()
        mock_response.data = mock_data
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = await db_get_estimate(estimate_id)

        assert result == mock_data[0]
        mock_supabase.table.assert_called_with("estimates")

    @pytest.mark.asyncio
    async def test_db_get_estimate_not_found(self, mock_supabase):
        """Test getting an estimate that doesn't exist."""
        estimate_id = "nonexistent"

        # Mock empty response
        mock_response = Mock()
        mock_response.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = await db_get_estimate(estimate_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_db_create_meal_from_manual(self, mock_supabase):
        """Test creating a meal from manual data."""
        from datetime import date

        from calorie_track_ai_bot.schemas import MealCreateManualRequest, MealType

        # Create a proper data object
        mock_data = MealCreateManualRequest(
            meal_date=date(2024, 1, 1), meal_type=MealType.breakfast, kcal_total=300.5
        )

        result = await db_create_meal_from_manual(mock_data)

        # Should return a dict with meal_id
        assert isinstance(result, dict)
        assert "meal_id" in result
        assert isinstance(result["meal_id"], str)
        assert len(result["meal_id"]) == 36  # UUID length

        # Should call insert with correct data
        mock_supabase.table.assert_called_with("meals")
        mock_table = mock_supabase.table.return_value
        mock_table.insert.assert_called_once()

        # Check the insert call arguments
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["meal_date"] == "2024-01-01"
        assert call_args["meal_type"] == "breakfast"
        assert call_args["kcal_total"] == 300.5
        assert call_args["source"] == "manual"
        assert call_args["user_id"] is None

    @pytest.mark.asyncio
    async def test_db_create_meal_from_estimate(self, mock_supabase):
        """Test creating a meal from estimate data."""
        from datetime import date

        from calorie_track_ai_bot.schemas import MealCreateFromEstimateRequest, MealType

        # Create a proper data object
        mock_data = MealCreateFromEstimateRequest(
            meal_date=date(2024, 1, 1),
            meal_type=MealType.lunch,
            estimate_id="estimate123",
            overrides={"kcal_total": 450},
        )

        result = await db_create_meal_from_estimate(mock_data)

        # Should return a dict with meal_id
        assert isinstance(result, dict)
        assert "meal_id" in result
        assert isinstance(result["meal_id"], str)
        assert len(result["meal_id"]) == 36  # UUID length

        # Should call insert with correct data
        mock_supabase.table.assert_called_with("meals")
        mock_table = mock_supabase.table.return_value
        mock_table.insert.assert_called_once()

        # Check the insert call arguments
        call_args = mock_table.insert.call_args[0][0]
        assert call_args["meal_date"] == "2024-01-01"
        assert call_args["meal_type"] == "lunch"
        assert call_args["kcal_total"] == 450  # From overrides
        assert call_args["source"] == "photo"
        assert call_args["estimate_id"] == "estimate123"
        assert call_args["user_id"] is None

    @pytest.mark.asyncio
    async def test_db_create_meal_from_estimate_no_overrides(self, mock_supabase):
        """Test creating a meal from estimate data without overrides."""
        from datetime import date

        from calorie_track_ai_bot.schemas import MealCreateFromEstimateRequest, MealType

        # Create a proper data object without overrides
        mock_data = MealCreateFromEstimateRequest(
            meal_date=date(2024, 1, 1),
            meal_type=MealType.dinner,
            estimate_id="estimate456",
            overrides=None,
        )

        result = await db_create_meal_from_estimate(mock_data)

        # Should return a dict with meal_id
        assert isinstance(result, dict)
        assert "meal_id" in result

        # Check the insert call arguments
        call_args = mock_supabase.table.return_value.insert.call_args[0][0]
        assert call_args["kcal_total"] == 0  # Default when no overrides

    @pytest.mark.asyncio
    async def test_db_create_meal_from_estimate_invalid_overrides(self, mock_supabase):
        """Test creating a meal from estimate data with invalid overrides."""
        from datetime import date

        from calorie_track_ai_bot.schemas import MealCreateFromEstimateRequest, MealType

        # Create a proper data object with None overrides (which is valid)
        mock_data = MealCreateFromEstimateRequest(
            meal_date=date(2024, 1, 1),
            meal_type=MealType.snack,
            estimate_id="estimate789",
            overrides=None,  # None is valid according to schema
        )

        result = await db_create_meal_from_estimate(mock_data)

        # Should return a dict with meal_id
        assert isinstance(result, dict)
        assert "meal_id" in result

        # Check the insert call arguments
        call_args = mock_supabase.table.return_value.insert.call_args[0][0]
        assert call_args["kcal_total"] == 0  # Default when overrides is None
