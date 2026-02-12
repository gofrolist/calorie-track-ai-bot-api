"""Statistics Service - Nutrition data aggregation and analytics.

Feature: 005-mini-app-improvements
Provides real-time aggregation of nutrition statistics for visualization.
"""

from datetime import date
from typing import Any

from ..schemas import (
    DailyDataPoint,
    DailyStatisticsResponse,
    MacroStatisticsResponse,
    StatisticsPeriod,
    StatisticsSummary,
)
from .config import logger
from .database import get_pool


class StatisticsService:
    """Service for aggregating and computing nutrition statistics."""

    async def get_daily_statistics(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> DailyStatisticsResponse:
        """Get daily nutrition statistics for a date range."""
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 365 days")

        try:
            pool = await get_pool()

            async with pool.connection() as conn:
                # Try RPC function first
                cur = await conn.execute(
                    "SELECT * FROM query_daily_statistics(%s, %s, %s)",
                    (user_id, start_date.isoformat(), end_date.isoformat()),
                )
                daily_data = [dict(r) for r in await cur.fetchall()]

                if not daily_data:
                    # Fallback: query raw meals and group in Python
                    cur = await conn.execute(
                        """SELECT created_at, kcal_total, protein_grams, fats_grams, carbs_grams
                           FROM meals
                           WHERE user_id = %s AND created_at >= %s AND created_at < %s""",
                        (user_id, start_date.isoformat(), end_date.isoformat()),
                    )
                    raw_meals = [dict(r) for r in await cur.fetchall()]
                    daily_data = self._group_by_date(raw_meals)

                # Get user's goal
                cur = await conn.execute(
                    """SELECT daily_kcal_target FROM goals
                       WHERE user_id = %s ORDER BY created_at DESC LIMIT 1""",
                    (user_id,),
                )
                goal_row = await cur.fetchone()
                goal_calories = dict(goal_row)["daily_kcal_target"] if goal_row else None

            # Convert to data points
            data_points = []
            for day in daily_data:
                goal_achievement = None
                if goal_calories and goal_calories > 0:
                    goal_achievement = (float(day["total_calories"]) / float(goal_calories)) * 100

                data_points.append(
                    DailyDataPoint(
                        date=date.fromisoformat(day["meal_date"])
                        if isinstance(day["meal_date"], str)
                        else day["meal_date"],
                        total_calories=float(day["total_calories"]),
                        total_protein=float(day["total_protein"]),
                        total_fat=float(day["total_fat"]),
                        total_carbs=float(day["total_carbs"]),
                        meal_count=int(day["meal_count"]),
                        goal_calories=float(goal_calories) if goal_calories else None,
                        goal_achievement=goal_achievement,
                    )
                )

            total_days = (end_date - start_date).days
            total_meals = sum(dp.meal_count for dp in data_points)
            total_calories = sum(dp.total_calories for dp in data_points)
            average_daily_calories = total_calories / total_days if total_days > 0 else 0

            average_goal_achievement = None
            if goal_calories:
                achievements = [
                    dp.goal_achievement for dp in data_points if dp.goal_achievement is not None
                ]
                average_goal_achievement = (
                    sum(achievements) / len(achievements) if achievements else 0
                )

            period = StatisticsPeriod(
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
            )

            summary = StatisticsSummary(
                total_meals=total_meals,
                average_daily_calories=average_daily_calories,
                average_goal_achievement=average_goal_achievement,
            )

            logger.info(
                f"Daily statistics retrieved for user {user_id[:8]}",
                extra={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "data_points": len(data_points),
                },
            )

            return DailyStatisticsResponse(data=data_points, period=period, summary=summary)

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to retrieve daily statistics: {e}",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    async def get_macro_statistics(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> MacroStatisticsResponse:
        """Get macronutrient breakdown for a date range."""
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 365 days")

        try:
            pool = await get_pool()

            async with pool.connection() as conn:
                cur = await conn.execute(
                    """SELECT kcal_total, protein_grams, fats_grams, carbs_grams
                       FROM meals
                       WHERE user_id = %s AND created_at >= %s AND created_at < %s""",
                    (user_id, start_date.isoformat(), end_date.isoformat()),
                )
                rows = [dict(r) for r in await cur.fetchall()]

            total_protein = sum(float(m.get("protein_grams", 0) or 0) for m in rows)
            total_fat = sum(float(m.get("fats_grams", 0) or 0) for m in rows)
            total_carbs = sum(float(m.get("carbs_grams", 0) or 0) for m in rows)
            total_calories = sum(float(m.get("kcal_total", 0) or 0) for m in rows)

            protein_percent = 0.0
            fat_percent = 0.0
            carbs_percent = 0.0

            if total_calories > 0:
                protein_percent = (total_protein * 4 / total_calories) * 100
                fat_percent = (total_fat * 9 / total_calories) * 100
                carbs_percent = (total_carbs * 4 / total_calories) * 100

            period = StatisticsPeriod(
                start_date=start_date,
                end_date=end_date,
                total_days=(end_date - start_date).days,
            )

            logger.info(
                f"Macro statistics retrieved for user {user_id[:8]}",
                extra={
                    "user_id": user_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "total_meals": len(rows),
                },
            )

            return MacroStatisticsResponse(
                protein_percent=protein_percent,
                fat_percent=fat_percent,
                carbs_percent=carbs_percent,
                protein_grams=total_protein,
                fat_grams=total_fat,
                carbs_grams=total_carbs,
                total_calories=total_calories,
                period=period,
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to retrieve macro statistics: {e}",
                extra={"user_id": user_id, "error": str(e)},
                exc_info=True,
            )
            raise

    def _group_by_date(self, meals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Group meals by date and aggregate nutrition data."""
        from collections import defaultdict

        daily_data: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "total_calories": 0.0,
                "total_protein": 0.0,
                "total_fat": 0.0,
                "total_carbs": 0.0,
                "meal_count": 0,
            }
        )

        for meal in meals:
            meal_date = str(meal["created_at"])[:10]
            daily_data[meal_date]["total_calories"] += float(meal.get("kcal_total", 0) or 0)
            daily_data[meal_date]["total_protein"] += float(meal.get("protein_grams", 0) or 0)
            daily_data[meal_date]["total_fat"] += float(meal.get("fats_grams", 0) or 0)
            daily_data[meal_date]["total_carbs"] += float(meal.get("carbs_grams", 0) or 0)
            daily_data[meal_date]["meal_count"] += 1

        return [{"meal_date": meal_date, **data} for meal_date, data in sorted(daily_data.items())]


# Global service instance
_statistics_service: StatisticsService | None = None


def get_statistics_service() -> StatisticsService:
    """Get the global statistics service instance."""
    global _statistics_service
    if _statistics_service is None:
        _statistics_service = StatisticsService()
    return _statistics_service
