"""Integration test for multi-photo without text caption (Scenario 2).

NOTE: These tests are marked as TODO - they require refactoring to use standard fixtures.
The multi-photo functionality is tested in:
- tests/api/v1/test_photos_multiphotos.py
- tests/services/test_estimator_multiphotos.py
"""

import pytest

# Mark all tests in this file as TODO/skip
pytestmark = pytest.mark.skip(
    reason="TODO: Refactor to use standard fixtures (api_client, authenticated_headers)"
)


@pytest.mark.asyncio
async def test_multiphotos_no_text_creates_meal(client, auth_headers, test_user, db_session):
    """
    Test multi-photo submission without text caption.

    Scenario 2: User sends 2 photos without caption.
    Expected: Single estimate created from photos only, meal with null description.
    """
    # Step 1: Create 2 photos without description
    photo_payload = {
        "photos": [
            {"filename": "photo1.jpg", "content_type": "image/jpeg"},
            {"filename": "photo2.jpg", "content_type": "image/jpeg"},
        ],
        "media_group_id": "no_text_group",
    }

    photos_response = await client.post("/api/v1/photos", json=photo_payload, headers=auth_headers)

    assert photos_response.status_code == 201
    photos_data = photos_response.json()
    photo_ids = [p["id"] for p in photos_data["photos"]]

    # Step 2: Create estimate without description (None/null)
    estimate_payload = {
        "photo_ids": photo_ids,
        "description": None,  # No text
        "media_group_id": "no_text_group",
    }

    estimate_response = await client.post(
        "/api/v1/estimates", json=estimate_payload, headers=auth_headers
    )

    assert estimate_response.status_code == 202
    estimate_data = estimate_response.json()

    assert estimate_data["photo_count"] == 2

    # Step 3: Verify meal can be created without description
    # The system should process photos-only submissions
    assert estimate_data["status"] == "queued"


@pytest.mark.asyncio
async def test_photos_only_ai_estimation(test_estimator):
    """Test AI estimation works with photos only (no text description)."""
    # Simulate photo URLs
    photo_urls = ["https://example.com/photo1.jpg", "https://example.com/photo2.jpg"]

    # Call estimator without description
    result = await test_estimator.estimate_from_photos(photo_urls, description=None)

    # Should still return valid estimate
    assert result is not None
    assert "calories_estimate" in result
    assert "macronutrients" in result


@pytest.mark.asyncio
async def test_meal_with_null_description(client, auth_headers, test_user, db_session):
    """Test meal retrieval with null description shows empty/null value."""
    from uuid import uuid4

    from calorie_track_ai_bot.schemas import Meal, Photo

    # Create meal without description
    meal_id = uuid4()
    meal = Meal(
        id=meal_id,
        user_id=test_user.id,
        calories=500.0,
        protein_grams=30.0,
        carbs_grams=50.0,
        fats_grams=15.0,
        description=None,  # Null description
    )
    db_session.add(meal)

    # Add photos
    photo = Photo(
        id=uuid4(),
        user_id=test_user.id,
        meal_id=meal_id,
        file_key="test/photo.jpg",
        display_order=0,
    )
    db_session.add(photo)
    db_session.commit()

    # Retrieve meal
    response = await client.get(f"/api/v1/meals/{meal_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    # Description should be null/None
    assert data["description"] is None

    # But should have photos
    assert len(data["photos"]) == 1
