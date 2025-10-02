"""Integration test for meal editing with macro updates (Scenario 7).

NOTE: These tests are marked as TODO - they require refactoring to use standard fixtures.
The meal editing functionality is tested in:
- tests/api/v1/test_meals_update.py
"""

from uuid import uuid4

import pytest

# Mark all tests in this file as TODO/skip
pytestmark = pytest.mark.skip(
    reason="TODO: Refactor to use standard fixtures (api_client, authenticated_headers)"
)


@pytest.mark.asyncio
async def test_meal_editing_updates_macros(client, auth_headers, test_user, db_session):
    """
    Test meal editing updates macronutrients and recalculates calories.

    Scenario 7: User edits meal description and macronutrients.
    Expected: Changes saved, calories recalculated, daily summary updated.
    """
    from calorie_track_ai_bot.schemas import Meal

    # Step 1: Create initial meal
    meal_id = uuid4()
    meal = Meal(
        id=meal_id,
        user_id=test_user.id,
        calories=500.0,
        protein_grams=30.0,
        carbs_grams=50.0,
        fats_grams=15.0,
        description="Original: Grilled chicken",
    )
    db_session.add(meal)
    db_session.commit()

    # Step 2: Update meal
    update_payload = {
        "description": "Updated: Grilled chicken pasta",
        "protein_grams": 50.0,
        "carbs_grams": 70.0,
        "fats_grams": 20.0,
    }

    response = await client.patch(
        f"/api/v1/meals/{meal_id}", json=update_payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Step 3: Verify updates
    assert data["description"] == "Updated: Grilled chicken pasta"
    assert data["macronutrients"]["protein"] == 50.0
    assert data["macronutrients"]["carbs"] == 70.0
    assert data["macronutrients"]["fats"] == 20.0

    # Step 4: Verify calorie recalculation (4*protein + 4*carbs + 9*fats)
    expected_calories = (50.0 * 4) + (70.0 * 4) + (20.0 * 9)
    assert data["calories"] == expected_calories  # 200 + 280 + 180 = 660


@pytest.mark.asyncio
async def test_meal_editing_partial_update(client, auth_headers, test_user, db_session):
    """Test updating only description keeps macros unchanged."""
    from calorie_track_ai_bot.schemas import Meal

    meal_id = uuid4()
    meal = Meal(
        id=meal_id,
        user_id=test_user.id,
        calories=500.0,
        protein_grams=30.0,
        carbs_grams=50.0,
        fats_grams=15.0,
        description="Original meal",
    )
    db_session.add(meal)
    db_session.commit()

    # Update only description
    update_payload = {"description": "Updated description only"}

    response = await client.patch(
        f"/api/v1/meals/{meal_id}", json=update_payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Description changed
    assert data["description"] == "Updated description only"

    # Macros unchanged
    assert data["macronutrients"]["protein"] == 30.0
    assert data["macronutrients"]["carbs"] == 50.0
    assert data["macronutrients"]["fats"] == 15.0


@pytest.mark.asyncio
async def test_meal_editing_macros_only(client, auth_headers, test_user, db_session):
    """Test updating only macros recalculates calories."""
    from calorie_track_ai_bot.schemas import Meal

    meal_id = uuid4()
    meal = Meal(
        id=meal_id,
        user_id=test_user.id,
        calories=500.0,
        protein_grams=30.0,
        carbs_grams=50.0,
        fats_grams=15.0,
        description="Meal description",
    )
    db_session.add(meal)
    db_session.commit()

    # Update only macros
    update_payload = {"protein_grams": 40.0, "carbs_grams": 60.0, "fats_grams": 18.0}

    response = await client.patch(
        f"/api/v1/meals/{meal_id}", json=update_payload, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Calories recalculated
    expected_calories = (40.0 * 4) + (60.0 * 4) + (18.0 * 9)
    assert data["calories"] == expected_calories


@pytest.mark.asyncio
async def test_meal_editing_forbidden_other_user(client, auth_headers, db_session):
    """Test editing another user's meal returns 403."""
    from calorie_track_ai_bot.schemas import Meal, User

    # Create another user
    other_user = User(id=uuid4(), telegram_id=999999, username="otheruser")
    db_session.add(other_user)

    # Create meal owned by other user
    meal_id = uuid4()
    meal = Meal(id=meal_id, user_id=other_user.id, calories=500.0)
    db_session.add(meal)
    db_session.commit()

    update_payload = {"description": "Trying to edit other's meal"}

    response = await client.patch(
        f"/api/v1/meals/{meal_id}", json=update_payload, headers=auth_headers
    )

    assert response.status_code == 403
