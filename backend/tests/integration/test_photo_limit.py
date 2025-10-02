"""Integration test for 5-photo limit enforcement (Scenario 3)."""

from uuid import uuid4

import pytest


@pytest.mark.skip(
    reason="TODO: Refactor to use standard fixtures - tested in test_photos_multiphotos.py"
)
@pytest.mark.asyncio
async def test_photo_limit_5_photos_accepted(client, auth_headers):
    """Test that exactly 5 photos are accepted."""
    photo_payload = {
        "photos": [{"filename": f"photo_{i}.jpg", "content_type": "image/jpeg"} for i in range(5)]
    }

    response = await client.post("/api/v1/photos", json=photo_payload, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert len(data["photos"]) == 5


@pytest.mark.skip(
    reason="TODO: Refactor to use standard fixtures - tested in test_photos_multiphotos.py"
)
@pytest.mark.asyncio
async def test_photo_limit_6_photos_rejected(client, auth_headers):
    """Test that 6 photos are rejected with error message."""
    photo_payload = {
        "photos": [{"filename": f"photo_{i}.jpg", "content_type": "image/jpeg"} for i in range(6)]
    }

    response = await client.post("/api/v1/photos", json=photo_payload, headers=auth_headers)

    assert response.status_code == 400
    error = response.json()

    assert "detail" in error
    assert "5" in error["detail"] or "five" in error["detail"].lower()
    assert "maximum" in error["detail"].lower() or "max" in error["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.skip(reason="TODO: Refactor to use standard fixtures")
async def test_estimate_limit_6_photos_rejected(client, auth_headers, test_user, db_session):
    """Test that estimate with 6 photo IDs is rejected."""
    from calorie_track_ai_bot.schemas import Photo

    # Create 6 photos in database
    photo_ids = []
    for i in range(6):
        photo_id = uuid4()
        photo = Photo(id=photo_id, user_id=test_user.id, file_key=f"test/photo_{i}.jpg")
        db_session.add(photo)
        photo_ids.append(str(photo_id))
    db_session.commit()

    # Try to create estimate with all 6
    estimate_payload = {"photo_ids": photo_ids}

    response = await client.post("/api/v1/estimates", json=estimate_payload, headers=auth_headers)

    assert response.status_code == 400
    error = response.json()
    assert "5" in error["detail"] or "five" in error["detail"].lower()


@pytest.mark.asyncio
async def test_photo_limit_validation_function():
    """Test validation function for photo count."""
    from fastapi import HTTPException

    from calorie_track_ai_bot.services.telegram import validate_photo_count

    # Valid counts - should not raise exception (returns None)
    assert validate_photo_count(1) is None
    assert validate_photo_count(3) is None
    assert validate_photo_count(5) is None

    # Invalid counts - should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        validate_photo_count(0)
    assert exc_info.value.status_code == 400
    assert "at least one photo" in exc_info.value.detail.lower()

    with pytest.raises(HTTPException) as exc_info:
        validate_photo_count(6)
    assert exc_info.value.status_code == 400
    assert "maximum 5 photos" in exc_info.value.detail.lower()

    with pytest.raises(HTTPException) as exc_info:
        validate_photo_count(10)
    assert exc_info.value.status_code == 400
    assert "maximum 5 photos" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_photo_limit_user_message():
    """Test user-friendly error message for photo limit."""
    from calorie_track_ai_bot.services.telegram import get_photo_limit_message

    message = get_photo_limit_message()

    assert "5 photos" in message
    assert "maximum" in message.lower() or "max" in message.lower()
    # Should have emoji or clear formatting
    assert len(message) > 20  # Reasonable message length
