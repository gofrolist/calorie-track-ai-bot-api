"""Integration test for multi-photo meal submission workflow (Scenario 1).

NOTE: These tests are marked as TODO - they require refactoring to use standard fixtures.
The multi-photo workflow is tested through:
- tests/api/v1/test_photos_multiphotos.py
- tests/services/test_estimator_multiphotos.py
"""

import asyncio

import pytest

# Mark all tests in this file as TODO/skip
pytestmark = pytest.mark.skip(reason="TODO: Refactor to use standard fixtures and proper mocking")


@pytest.mark.asyncio
async def test_multiphotos_workflow_end_to_end(
    api_client, authenticated_headers, test_user_data, db_transaction
):
    """
    Test complete multi-photo meal submission workflow.

    Scenario 1: User sends 3 photos in one message with text caption.
    Expected: Single estimate created with all photos, macronutrients returned.
    """
    # Step 1: Create 3 photos using the existing single-photo API
    photo_ids = []
    for _i in range(3):
        photo_payload = {"content_type": "image/jpeg"}

        photos_response = api_client.post(
            "/api/v1/photos", json=photo_payload, headers=authenticated_headers
        )

        assert photos_response.status_code == 201
        photo_data = photos_response.json()
        photo_ids.append(photo_data["photo_id"])

    # Step 2: Create estimate for all 3 photos
    estimate_payload = {"photo_ids": photo_ids, "description": "Chicken pasta dinner"}

    estimate_response = api_client.post(
        "/api/v1/estimates", json=estimate_payload, headers=authenticated_headers
    )

    assert estimate_response.status_code == 202
    estimate_data = estimate_response.json()

    assert estimate_data["status"] == "queued"
    assert estimate_data["photo_count"] == 3

    # Step 3: Poll estimate result (simulated worker completion)
    # In real workflow, worker processes this
    await asyncio.sleep(0.1)  # Simulate processing

    # Step 4: Verify meal created with all photos
    meals_response = api_client.get("/api/v1/meals", headers=authenticated_headers)
    assert meals_response.status_code == 200
    meals_data = meals_response.json()

    # Should have at least one meal (our test meal)
    assert len(meals_data["meals"]) > 0


@pytest.mark.asyncio
async def test_multiphotos_media_group_aggregation(test_user_data):
    """Test that photos with same media_group_id are aggregated."""
    from unittest.mock import Mock

    from calorie_track_ai_bot.services.telegram import TelegramService

    service = TelegramService()
    media_group_id = "test_media_group_456"

    # Simulate 3 Telegram updates with same media_group_id
    updates = []
    for i in range(3):
        update = Mock()
        update.message = Mock()
        update.message.media_group_id = media_group_id
        update.message.photo = [Mock()]
        update.message.caption = "Meal description" if i == 0 else None
        updates.append(update)

    # Get media group ID from first update
    detected_id = await service.get_media_group_id(updates[0])
    assert detected_id == media_group_id

    # All updates should have same media_group_id
    for update in updates:
        assert await service.get_media_group_id(update) == media_group_id


@pytest.mark.asyncio
async def test_multiphotos_caption_extraction():
    """Test caption is extracted from first photo in media group."""
    from unittest.mock import Mock

    from calorie_track_ai_bot.services.telegram import TelegramService

    service = TelegramService()

    updates = [
        Mock(message_id=1, caption="This is the meal description", media_group_id="group1"),
        Mock(message_id=2, caption=None, media_group_id="group1"),
    ]

    caption = await service.extract_media_group_caption(updates)
    assert caption == "This is the meal description"
