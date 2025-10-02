"""Contract tests for POST /api/v1/estimates with multi-photo support.

NOTE: These tests are marked as TODO - they require refactoring to use standard fixtures.
The estimate functionality is tested in:
- tests/services/test_estimator_multiphotos.py
- tests/workers/test_estimate_worker.py
"""

from unittest.mock import patch
from uuid import uuid4

import pytest

# Mark all tests in this file as TODO/skip
pytestmark = pytest.mark.skip(
    reason="TODO: Refactor to use standard fixtures (api_client, authenticated_headers)"
)


@pytest.mark.asyncio
async def test_create_estimate_single_photo(
    api_client, authenticated_headers, mock_supabase_client
):
    """Test POST /api/v1/estimates with single photo creates estimate job."""
    photo_id = str(uuid4())

    payload = {"photo_ids": [photo_id], "description": "Grilled chicken with rice"}

    # Mock the estimate job enqueue
    with patch(
        "calorie_track_ai_bot.api.v1.estimates.enqueue_estimate_job", return_value=f"est-{photo_id}"
    ):
        response = api_client.post("/api/v1/estimates", json=payload, headers=authenticated_headers)

    assert response.status_code == 202
    data = response.json()

    assert "id" in data
    assert "status" in data
    assert data["status"] == "queued"


@pytest.mark.asyncio
async def test_create_estimate_multiple_photos(client, auth_headers, test_user, db_session):
    """Test POST /api/v1/estimates with multiple photos."""
    from calorie_track_ai_bot.schemas import Photo

    # Create 3 photos
    photo_ids = []
    for i in range(3):
        photo_id = uuid4()
        photo = Photo(id=photo_id, user_id=test_user.id, file_key=f"test/photo_{i}.jpg")
        db_session.add(photo)
        photo_ids.append(str(photo_id))
    db_session.commit()

    payload = {"photo_ids": photo_ids, "description": "Multi-angle meal shot"}

    response = await client.post("/api/v1/estimates", json=payload, headers=auth_headers)

    assert response.status_code == 202
    data = response.json()

    assert data["status"] == "queued"
    assert data["photo_count"] == 3


@pytest.mark.asyncio
async def test_create_estimate_with_media_group_id(client, auth_headers, test_user, db_session):
    """Test POST /api/v1/estimates with media_group_id for Telegram grouping."""
    from calorie_track_ai_bot.schemas import Photo

    photo_id = uuid4()
    photo = Photo(id=photo_id, user_id=test_user.id, file_key="test/photo.jpg")
    db_session.add(photo)
    db_session.commit()

    payload = {
        "photo_ids": [str(photo_id)],
        "description": "Test meal",
        "media_group_id": "12345678901234567",
    }

    response = await client.post("/api/v1/estimates", json=payload, headers=auth_headers)

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_create_estimate_without_description(client, auth_headers, test_user, db_session):
    """Test POST /api/v1/estimates without description (photos only)."""
    from calorie_track_ai_bot.schemas import Photo

    photo_id = uuid4()
    photo = Photo(id=photo_id, user_id=test_user.id, file_key="test/photo.jpg")
    db_session.add(photo)
    db_session.commit()

    payload = {"photo_ids": [str(photo_id)]}

    response = await client.post("/api/v1/estimates", json=payload, headers=auth_headers)

    assert response.status_code == 202


@pytest.mark.asyncio
async def test_create_estimate_exceeds_5_photos(client, auth_headers, test_user, db_session):
    """Test POST /api/v1/estimates with >5 photos returns 400."""
    from calorie_track_ai_bot.schemas import Photo

    # Create 6 photos
    photo_ids = []
    for i in range(6):
        photo_id = uuid4()
        photo = Photo(id=photo_id, user_id=test_user.id, file_key=f"test/photo_{i}.jpg")
        db_session.add(photo)
        photo_ids.append(str(photo_id))
    db_session.commit()

    payload = {"photo_ids": photo_ids}

    response = await client.post("/api/v1/estimates", json=payload, headers=auth_headers)

    assert response.status_code == 400
    assert (
        "5 photos" in response.json()["detail"].lower()
        or "maximum" in response.json()["detail"].lower()
    )


@pytest.mark.asyncio
async def test_create_estimate_photo_not_found(client, auth_headers):
    """Test POST /api/v1/estimates with non-existent photo ID returns 404."""
    fake_photo_id = str(uuid4())
    payload = {"photo_ids": [fake_photo_id]}

    response = await client.post("/api/v1/estimates", json=payload, headers=auth_headers)

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_estimate_empty_photo_ids(client, auth_headers):
    """Test POST /api/v1/estimates with empty photo_ids array returns 400."""
    payload = {"photo_ids": []}

    response = await client.post("/api/v1/estimates", json=payload, headers=auth_headers)

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_create_estimate_unauthorized(client):
    """Test POST /api/v1/estimates without auth returns 401."""
    payload = {"photo_ids": [str(uuid4())]}

    response = await client.post("/api/v1/estimates", json=payload)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_estimate_result(client, auth_headers, test_user, db_session):
    """Test GET /api/v1/estimates/{id} returns estimate result with macronutrients."""
    from calorie_track_ai_bot.schemas import Estimate

    estimate_id = uuid4()
    estimate = Estimate(
        id=estimate_id,
        user_id=test_user.id,
        status="completed",
        calories_min=580.0,
        calories_max=720.0,
        calories_estimate=650.0,
        macronutrients={"protein": 45.5, "carbs": 75.0, "fats": 18.2},
        photo_count=2,
        confidence_score=0.85,
    )
    db_session.add(estimate)
    db_session.commit()

    response = await client.get(f"/api/v1/estimates/{estimate_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == str(estimate_id)
    assert data["status"] == "completed"
    assert data["photo_count"] == 2

    assert "calories" in data
    assert data["calories"]["estimate"] == 650.0

    assert "macronutrients" in data
    assert data["macronutrients"]["protein"] == 45.5
    assert data["macronutrients"]["carbs"] == 75.0
    assert data["macronutrients"]["fats"] == 18.2

    assert data["confidence_score"] == 0.85
