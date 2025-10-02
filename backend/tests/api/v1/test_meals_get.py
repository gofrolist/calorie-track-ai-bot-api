"""Contract tests for GET /api/v1/meals/{id} endpoint."""

from datetime import UTC
from unittest.mock import patch
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_get_meal_by_id_success(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals/{id} returns meal details with photos."""
    from datetime import datetime

    from calorie_track_ai_bot.schemas import Macronutrients, MealPhotoInfo, MealWithPhotos

    meal_id = uuid4()
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock the database function
    mock_meal = MealWithPhotos(
        id=meal_id,
        userId=user_uuid,
        calories=650.0,
        description="Chicken pasta dinner",
        createdAt=datetime.now(UTC),
        macronutrients=Macronutrients(protein=45.5, carbs=75.0, fats=18.2),
        photos=[
            MealPhotoInfo(
                id=uuid4(),
                displayOrder=0,
                thumbnailUrl="https://example.com/thumb1.jpg",
                fullUrl="https://example.com/full1.jpg",
            ),
            MealPhotoInfo(
                id=uuid4(),
                displayOrder=1,
                thumbnailUrl="https://example.com/thumb2.jpg",
                fullUrl="https://example.com/full2.jpg",
            ),
        ],
    )

    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=mock_meal),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        response = api_client.get(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(meal_id)
    assert data["userId"] == user_uuid
    assert data["calories"] == 650.0
    assert data["description"] == "Chicken pasta dinner"

    # Check macronutrients
    assert "macronutrients" in data
    assert data["macronutrients"]["protein"] == 45.5
    assert data["macronutrients"]["carbs"] == 75.0
    assert data["macronutrients"]["fats"] == 18.2

    # Check photos
    assert "photos" in data
    assert len(data["photos"]) == 2
    assert data["photos"][0]["displayOrder"] == 0
    assert data["photos"][1]["displayOrder"] == 1


@pytest.mark.asyncio
async def test_get_meal_includes_presigned_urls(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals/{id} includes presigned URLs for photos."""
    from datetime import datetime

    from calorie_track_ai_bot.schemas import Macronutrients, MealPhotoInfo, MealWithPhotos

    meal_id = uuid4()
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock the database function
    mock_meal = MealWithPhotos(
        id=meal_id,
        userId=user_uuid,
        calories=500.0,
        createdAt=datetime.now(UTC),
        macronutrients=Macronutrients(protein=0.0, carbs=0.0, fats=0.0),
        photos=[
            MealPhotoInfo(
                id=uuid4(),
                displayOrder=0,
                thumbnailUrl="https://example.com/thumb.jpg",
                fullUrl="https://example.com/full.jpg",
            )
        ],
    )

    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=mock_meal),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        response = api_client.get(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

    assert response.status_code == 200
    data = response.json()

    assert len(data["photos"]) == 1
    photo_data = data["photos"][0]

    assert "thumbnailUrl" in photo_data
    assert "fullUrl" in photo_data
    assert isinstance(photo_data["thumbnailUrl"], str)
    assert isinstance(photo_data["fullUrl"], str)


@pytest.mark.asyncio
async def test_get_meal_not_found(api_client, authenticated_headers, mock_supabase_client):
    """Test GET /api/v1/meals/{id} with non-existent ID returns 404."""
    fake_id = uuid4()

    with patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=None):
        response = api_client.get(f"/api/v1/meals/{fake_id}", headers=authenticated_headers)

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_meal_forbidden_other_user(
    api_client, authenticated_headers, mock_supabase_client
):
    """Test GET /api/v1/meals/{id} for another user's meal returns 403."""
    from datetime import datetime

    from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

    # Create meal owned by another user
    meal_id = uuid4()
    other_user_id = uuid4()

    mock_meal = MealWithPhotos(
        id=meal_id,
        userId=other_user_id,  # Different user
        calories=500.0,
        createdAt=datetime.now(UTC),
        macronutrients=Macronutrients(protein=0.0, carbs=0.0, fats=0.0),
        photos=[],
    )

    with patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=mock_meal):
        response = api_client.get(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

    assert response.status_code == 403
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_meal_unauthorized(api_client):
    """Test GET /api/v1/meals/{id} without auth returns 401."""
    fake_id = uuid4()
    response = api_client.get(f"/api/v1/meals/{fake_id}")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_meal_invalid_uuid(api_client, authenticated_headers, mock_supabase_client):
    """Test GET /api/v1/meals/{id} with invalid UUID returns 400 or 422."""
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=None),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        response = api_client.get("/api/v1/meals/not-a-uuid", headers=authenticated_headers)

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_get_meal_with_no_photos(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals/{id} for meal with no photos returns empty photos array."""
    from datetime import datetime

    from calorie_track_ai_bot.schemas import Macronutrients, MealWithPhotos

    meal_id = uuid4()
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    # Mock the database function
    mock_meal = MealWithPhotos(
        id=meal_id,
        userId=user_uuid,
        calories=300.0,
        description="Text-only meal",
        createdAt=datetime.now(UTC),
        macronutrients=Macronutrients(protein=0.0, carbs=0.0, fats=0.0),
        photos=[],
    )

    with (
        patch("calorie_track_ai_bot.api.v1.meals.db_get_meal_with_photos", return_value=mock_meal),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        response = api_client.get(f"/api/v1/meals/{meal_id}", headers=authenticated_headers)

    assert response.status_code == 200
    data = response.json()

    assert "photos" in data
    assert data["photos"] == []
