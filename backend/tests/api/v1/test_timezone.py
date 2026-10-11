"""Tests for bucketing meals into the user's local calendar days via the x-timezone header."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from calorie_track_ai_bot.api.v1.deps import get_user_timezone
from calorie_track_ai_bot.schemas import (
    DailyStatisticsResponse,
    StatisticsPeriod,
    StatisticsSummary,
)
from calorie_track_ai_bot.services.statistics_service import StatisticsService

USER_UUID = "550e8400-e29b-41d4-a716-446655440000"


def _request(headers: dict[str, str]) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw})


class TestGetUserTimezone:
    def test_valid_zone(self):
        assert get_user_timezone(_request({"x-timezone": "America/New_York"})) == (
            "America/New_York"
        )

    @pytest.mark.parametrize("value", [None, "", "   ", "Not/AZone", "../etc/passwd", "America"])
    def test_missing_or_invalid_falls_back_to_utc(self, value):
        headers = {} if value is None else {"x-timezone": value}
        assert get_user_timezone(_request(headers)) == "UTC"


class TestStatisticsTimezone:
    def test_daily_statistics_route_passes_header_zone(self, api_client, authenticated_headers):
        empty = DailyStatisticsResponse(
            data=[],
            period=StatisticsPeriod(
                start_date=date(2026, 10, 5), end_date=date(2026, 10, 12), total_days=7
            ),
            summary=StatisticsSummary(total_meals=0, average_daily_calories=0),
        )
        service = MagicMock()
        service.get_daily_statistics = AsyncMock(return_value=empty)

        with (
            patch("calorie_track_ai_bot.api.v1.deps.resolve_user_id", return_value=USER_UUID),
            patch(
                "calorie_track_ai_bot.api.v1.statistics.get_statistics_service",
                return_value=service,
            ),
        ):
            response = api_client.get(
                "/api/v1/statistics/daily?start_date=2026-10-05&end_date=2026-10-12",
                headers={**authenticated_headers, "x-timezone": "America/New_York"},
            )

        assert response.status_code == 200
        assert service.get_daily_statistics.await_args.kwargs["tz"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_daily_statistics_groups_by_local_date(self):
        cursor = AsyncMock()
        cursor.fetchall = AsyncMock(
            side_effect=[
                [
                    {
                        "meal_date": date(2026, 10, 11),
                        "total_calories": 500,
                        "total_protein": 20,
                        "total_fat": 10,
                        "total_carbs": 60,
                        "meal_count": 2,
                    }
                ],
            ]
        )
        cursor.fetchone = AsyncMock(return_value=None)
        conn = AsyncMock()
        conn.execute = AsyncMock(return_value=cursor)
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=conn)
        ctx.__aexit__ = AsyncMock(return_value=False)
        pool = MagicMock()
        pool.connection.return_value = ctx

        with patch(
            "calorie_track_ai_bot.services.statistics_service.get_pool",
            AsyncMock(return_value=pool),
        ):
            result = await StatisticsService().get_daily_statistics(
                USER_UUID, date(2026, 10, 5), date(2026, 10, 12), tz="America/New_York"
            )

        sql, params = conn.execute.call_args_list[0][0]
        assert "AT TIME ZONE" in sql
        assert params == (
            "America/New_York",
            USER_UUID,
            "America/New_York",
            date(2026, 10, 5),
            "America/New_York",
            date(2026, 10, 12),
        )
        assert [(p.date, p.meal_count) for p in result.data] == [(date(2026, 10, 11), 2)]
