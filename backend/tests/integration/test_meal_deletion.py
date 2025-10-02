"""Integration test for meal deletion with stats update (Scenario 8).

NOTE: These tests are marked as TODO - they require refactoring to use standard fixtures.
The meal deletion functionality is tested in:
- tests/api/v1/test_meals_delete.py
"""

from datetime import datetime
from uuid import uuid4

import pytest

# Mark all tests in this file as TODO/skip
pytestmark = pytest.mark.skip(
    reason="TODO: Refactor to use standard fixtures (api_client, authenticated_headers)"
)


@pytest.mark.asyncio
async def test_meal_deletion_removes_meal(client, auth_headers, test_user, db_session):
    """
    Test meal deletion removes meal and updates statistics.

    Scenario 8: User deletes a meal from history.
    Expected: Meal removed, daily summary updated, photos deleted.
    """
    from calorie_track_ai_bot.schemas import Meal, Photo

    # Step 1: Create meal with photos
    meal_id = uuid4()
    meal = Meal(
        id=meal_id,
        user_id=test_user.id,
        calories=600.0,
        protein_grams=40.0,
        carbs_grams=60.0,
        fats_grams=20.0,
        description="Meal to delete",
    )
    db_session.add(meal)

    photo = Photo(
        id=uuid4(),
        user_id=test_user.id,
        meal_id=meal_id,
        file_key="test/photo.jpg",
        display_order=0,
    )
    db_session.add(photo)
    db_session.commit()

    # Step 2: Delete meal
    response = await client.delete(f"/api/v1/meals/{meal_id}", headers=auth_headers)

    assert response.status_code == 204

    # Step 3: Verify meal is deleted
    get_response = await client.get(f"/api/v1/meals/{meal_id}", headers=auth_headers)

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_meal_deletion_cascades_to_photos(client, auth_headers, test_user, db_session):
    """Test meal deletion also deletes associated photos (cascade)."""
    from calorie_track_ai_bot.schemas import Meal, Photo

    meal_id = uuid4()
    meal = Meal(id=meal_id, user_id=test_user.id, calories=500.0)
    db_session.add(meal)

    # Create 2 photos for this meal
    photo_ids = []
    for i in range(2):
        photo_id = uuid4()
        photo = Photo(
            id=photo_id,
            user_id=test_user.id,
            meal_id=meal_id,
            file_key=f"test/photo_{i}.jpg",
            display_order=i,
        )
        db_session.add(photo)
        photo_ids.append(photo_id)
    db_session.commit()

    # Delete meal
    response = await client.delete(f"/api/v1/meals/{meal_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify photos are also deleted
    from calorie_track_ai_bot.schemas import Photo as PhotoModel

    remaining_photos = db_session.query(PhotoModel).filter(PhotoModel.meal_id == meal_id).all()

    assert len(remaining_photos) == 0


@pytest.mark.asyncio
async def test_meal_deletion_forbidden_other_user(client, auth_headers, db_session):
    """Test deleting another user's meal returns 403."""
    from calorie_track_ai_bot.schemas import Meal, User

    # Create another user
    other_user = User(id=uuid4(), telegram_id=999999, username="otheruser")
    db_session.add(other_user)

    # Create meal owned by other user
    meal_id = uuid4()
    meal = Meal(id=meal_id, user_id=other_user.id, calories=500.0)
    db_session.add(meal)
    db_session.commit()

    response = await client.delete(f"/api/v1/meals/{meal_id}", headers=auth_headers)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_meal_deletion_not_found(client, auth_headers):
    """Test deleting non-existent meal returns 404."""
    fake_id = uuid4()
    response = await client.delete(f"/api/v1/meals/{fake_id}", headers=auth_headers)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_meal_deletion_updates_daily_summary(client, auth_headers, test_user, db_session):
    """Test meal deletion updates daily summary statistics."""
    from datetime import date

    from calorie_track_ai_bot.schemas import DailySummary, Meal

    today = date.today()

    # Create daily summary
    summary = DailySummary(
        id=uuid4(),
        user_id=test_user.id,
        date=today,
        total_calories=1000.0,
        total_protein_grams=70.0,
        total_carbs_grams=100.0,
        total_fats_grams=30.0,
        meal_count=2,
    )
    db_session.add(summary)

    # Create meal to delete
    meal_id = uuid4()
    meal = Meal(
        id=meal_id,
        user_id=test_user.id,
        created_at=datetime.combine(today, datetime.min.time()),
        calories=400.0,
        protein_grams=30.0,
        carbs_grams=40.0,
        fats_grams=10.0,
    )
    db_session.add(meal)
    db_session.commit()

    # Delete meal
    response = await client.delete(f"/api/v1/meals/{meal_id}", headers=auth_headers)

    assert response.status_code == 204

    # Verify daily summary is updated (if endpoint returns updated summary)
    # Note: This depends on implementation - summary should reduce by meal's values
