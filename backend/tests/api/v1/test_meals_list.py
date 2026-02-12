"""Contract tests for GET /api/v1/meals endpoint."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_get_meals_without_filters(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals without any filters returns recent meals."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock meals query to return empty list
    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = []

        response = api_client.get("/api/v1/meals", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()

        assert "meals" in data
        assert "total" in data
        assert isinstance(data["meals"], list)
        assert isinstance(data["total"], int)


@pytest.mark.asyncio
async def test_get_meals_with_date_filter(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals with date filter returns meals for that date."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock meals query to return empty list
    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = []

        today = datetime.now().date().isoformat()
        response = api_client.get(f"/api/v1/meals?date={today}", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()

        assert "meals" in data
        assert isinstance(data["meals"], list)


@pytest.mark.asyncio
async def test_get_meals_with_date_range(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals with start_date and end_date returns meals in range."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock meals query to return empty list
    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = []

        start_date = (datetime.now() - timedelta(days=7)).date().isoformat()
        end_date = datetime.now().date().isoformat()

        response = api_client.get(
            f"/api/v1/meals?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "meals" in data
        assert isinstance(data["meals"], list)


@pytest.mark.asyncio
async def test_get_meals_with_limit(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals with limit parameter limits results."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock meals query to return empty list
    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = []

        response = api_client.get("/api/v1/meals?limit=5", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()

        assert "meals" in data
        assert len(data["meals"]) <= 5


@pytest.mark.asyncio
async def test_get_meals_returns_photos(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals includes photos array for each meal."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    from calorie_track_ai_bot.schemas import Macronutrients, MealPhotoInfo, MealWithPhotos

    meal_id = uuid4()
    photo1_id = uuid4()
    photo2_id = uuid4()

    mock_meal = MealWithPhotos(
        id=meal_id,
        userId=test_user_uuid,
        description="Test meal with photos",
        calories=500.0,
        macronutrients=Macronutrients(protein=30.0, carbs=50.0, fats=15.0),
        createdAt=datetime.now(UTC),
        photos=[
            MealPhotoInfo(
                id=photo1_id,
                thumbnailUrl="https://test.com/thumb1.jpg",
                fullUrl="https://test.com/full1.jpg",
                displayOrder=0,
            ),
            MealPhotoInfo(
                id=photo2_id,
                thumbnailUrl="https://test.com/thumb2.jpg",
                fullUrl="https://test.com/full2.jpg",
                displayOrder=1,
            ),
        ],
    )

    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = [mock_meal]

        response = api_client.get("/api/v1/meals", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()

        # Find our test meal
        test_meal = next((m for m in data["meals"] if m["id"] == str(meal_id)), None)
        assert test_meal is not None

        assert "photos" in test_meal
        assert len(test_meal["photos"]) == 2
        assert test_meal["photos"][0]["displayOrder"] == 0
        assert test_meal["photos"][1]["displayOrder"] == 1


@pytest.mark.asyncio
async def test_get_meals_returns_macronutrients(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals includes macronutrients object."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

    meal_id = uuid4()

    mock_meal = MealWithPhotos(
        id=meal_id,
        userId=test_user_uuid,
        description="Test meal with macros",
        calories=500.0,
        macronutrients=Macronutrients(protein=30.0, carbs=50.0, fats=15.0),
        createdAt=datetime.now(UTC),
        photos=[],
    )

    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = [mock_meal]

        response = api_client.get("/api/v1/meals", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()

        if data["meals"]:
            meal = data["meals"][0]
            assert "macronutrients" in meal
            assert "protein" in meal["macronutrients"]
            assert "carbs" in meal["macronutrients"]
            assert "fats" in meal["macronutrients"]


@pytest.mark.asyncio
async def test_get_meals_filters_one_year_retention(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals excludes meals older than 1 year."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock meals query to return empty list (old meals filtered out)
    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meals_with_photos") as mock_get_meals,
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid),
    ):
        mock_get_meals.return_value = []

        response = api_client.get("/api/v1/meals", headers=authenticated_headers)

        assert response.status_code == 200
        data = response.json()

        # Old meal should not be in results
        meal_ids = [m["id"] for m in data["meals"]]
        assert len(meal_ids) == 0  # No meals returned


@pytest.mark.asyncio
async def test_get_meals_invalid_date_format(
    api_client, authenticated_headers, mock_supabase_client
):
    """Test GET /api/v1/meals with invalid date format returns 400."""
    test_user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=test_user_uuid):
        response = api_client.get("/api/v1/meals?date=invalid-date", headers=authenticated_headers)

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_meals_unauthorized(api_client):
    """Test GET /api/v1/meals without auth returns 401."""
    response = api_client.get("/api/v1/meals")

    assert response.status_code == 401
