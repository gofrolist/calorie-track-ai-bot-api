"""Contract tests for GET /api/v1/meals/calendar endpoint."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


@pytest.mark.asyncio
async def test_get_meals_calendar_success(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test GET /api/v1/meals/calendar returns daily summaries."""
    from calorie_track_ai_bot.schemas import MealCalendarDay

    # Mock the database function
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    mock_calendar_data = [
        MealCalendarDay(
            meal_date=yesterday,
            meal_count=1,
            total_calories=600.0,
            total_protein=40.0,
            total_carbs=60.0,
            total_fats=20.0,
        ),
        MealCalendarDay(
            meal_date=today,
            meal_count=1,
            total_calories=500.0,
            total_protein=30.0,
            total_carbs=50.0,
            total_fats=15.0,
        ),
    ]

    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with (
        patch(
            "calorie_track_ai_bot.api.v1.meals.db_get_meals_calendar_summary",
            return_value=mock_calendar_data,
        ),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        start_date = yesterday.isoformat()
        end_date = today.isoformat()

        response = api_client.get(
            f"/api/v1/meals/calendar?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers,
        )

    assert response.status_code == 200
    data = response.json()

    assert "dates" in data
    assert isinstance(data["dates"], list)
    assert len(data["dates"]) == 2


@pytest.mark.asyncio
async def test_calendar_aggregates_meals_by_date(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test calendar endpoint aggregates multiple meals per date."""
    from calorie_track_ai_bot.schemas import MealCalendarDay

    today = datetime.now().date()

    # Mock aggregated data for 3 meals on the same day
    mock_calendar_data = [
        MealCalendarDay(
            meal_date=today,
            meal_count=3,
            total_calories=900.0,
            total_protein=60.0,
            total_carbs=90.0,
            total_fats=30.0,
        )
    ]

    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with (
        patch(
            "calorie_track_ai_bot.api.v1.meals.db_get_meals_calendar_summary",
            return_value=mock_calendar_data,
        ),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        response = api_client.get(
            f"/api/v1/meals/calendar?start_date={today.isoformat()}&end_date={today.isoformat()}",
            headers=authenticated_headers,
        )

    assert response.status_code == 200
    data = response.json()

    # Find today's summary
    today_summary = next((d for d in data["dates"] if d["meal_date"] == today.isoformat()), None)
    assert today_summary is not None

    assert today_summary["meal_count"] == 3
    assert today_summary["total_calories"] == 900.0
    assert today_summary["total_protein"] == 60.0
    assert today_summary["total_carbs"] == 90.0
    assert today_summary["total_fats"] == 30.0


@pytest.mark.asyncio
async def test_calendar_missing_start_date(api_client, authenticated_headers, mock_supabase_client):
    """Test calendar endpoint without start_date returns 422."""
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid):
        end_date = datetime.now().date().isoformat()
        response = api_client.get(
            f"/api/v1/meals/calendar?end_date={end_date}", headers=authenticated_headers
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_calendar_missing_end_date(api_client, authenticated_headers, mock_supabase_client):
    """Test calendar endpoint without end_date returns 422."""
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid):
        start_date = datetime.now().date().isoformat()
        response = api_client.get(
            f"/api/v1/meals/calendar?start_date={start_date}", headers=authenticated_headers
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_calendar_invalid_date_format(
    api_client, authenticated_headers, mock_supabase_client
):
    """Test calendar endpoint with invalid date format returns 400."""
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid):
        response = api_client.get(
            "/api/v1/meals/calendar?start_date=invalid&end_date=2025-09-30",
            headers=authenticated_headers,
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_calendar_max_one_year_range(api_client, authenticated_headers, mock_supabase_client):
    """Test calendar endpoint rejects range > 1 year."""
    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid):
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=400)

        response = api_client.get(
            f"/api/v1/meals/calendar?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=authenticated_headers,
        )

    assert response.status_code == 400
    assert "1 year" in response.json()["detail"].lower() or "365" in response.json()["detail"]


@pytest.mark.asyncio
async def test_calendar_filters_one_year_retention(
    api_client, authenticated_headers, test_user_data, mock_supabase_client
):
    """Test calendar rejects date ranges > 1 year."""
    from calorie_track_ai_bot.schemas import MealCalendarDay

    # Mock calendar data that excludes old meals (simulating the database filtering)
    today = datetime.now().date()
    mock_calendar_data = [
        MealCalendarDay(
            meal_date=today,
            meal_count=1,
            total_calories=500.0,
            total_protein=0.0,
            total_carbs=0.0,
            total_fats=0.0,
        )
    ]

    user_uuid = "550e8400-e29b-41d4-a716-446655440000"

    with (
        patch(
            "calorie_track_ai_bot.api.v1.meals.db_get_meals_calendar_summary",
            return_value=mock_calendar_data,
        ),
        patch("calorie_track_ai_bot.services.db.resolve_user_id", return_value=user_uuid),
    ):
        start_date = (datetime.now() - timedelta(days=450)).date().isoformat()
        end_date = datetime.now().date().isoformat()

        response = api_client.get(
            f"/api/v1/meals/calendar?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers,
        )

    assert response.status_code == 400
    assert "1 year" in response.json()["detail"].lower() or "365" in response.json()["detail"]


@pytest.mark.asyncio
async def test_calendar_unauthorized(api_client):
    """Test calendar endpoint without auth returns 401."""
    today = datetime.now().date().isoformat()
    response = api_client.get(f"/api/v1/meals/calendar?start_date={today}&end_date={today}")

    assert response.status_code == 401
