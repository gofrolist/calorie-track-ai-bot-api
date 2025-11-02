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
from .db import sb


class StatisticsService:
    """Service for aggregating and computing nutrition statistics."""

    def __init__(self):
        if sb is None:
            raise RuntimeError(
                "Supabase configuration not available. Database functionality is disabled."
            )
        self.supabase = sb

    async def get_daily_statistics(
        self,
        user_id: str,
        start_date: date,
        end_date: date,
    ) -> DailyStatisticsResponse:
        """Get daily nutrition statistics for a date range.

        Args:
            user_id: User identifier
            start_date: Start date (inclusive)
            end_date: End date (exclusive)

        Returns:
            Daily statistics response with data points and summary

        Raises:
            ValueError: If date range invalid
            Exception: If query fails
        """
        # Validate date range
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 365 days")

        try:
            # Query meals grouped by date
            # Note: RPC function would use this SQL query for better performance:
            # SELECT DATE(created_at) as meal_date, SUM(estimated_calories) as total_calories,
            # SUM(estimated_protein) as total_protein, SUM(estimated_fat) as total_fat,
            # SUM(estimated_carbs) as total_carbs, COUNT(*) as meal_count
            # FROM meals WHERE user_id = p_user_id AND created_at >= p_start_date
            # AND created_at < p_end_date GROUP BY DATE(created_at) ORDER BY DATE(created_at) ASC

            result = self.supabase.rpc(
                "query_daily_statistics",
                {
                    "p_user_id": user_id,
                    "p_start_date": start_date.isoformat(),
                    "p_end_date": end_date.isoformat(),
                },
            ).execute()

            # If RPC not available, use table query as fallback
            if not result.data:
                result = (
                    self.supabase.table("meals")
                    .select(
                        "created_at, estimated_calories, estimated_protein, estimated_fat, estimated_carbs"
                    )
                    .eq("user_id", user_id)
                    .gte("created_at", start_date.isoformat())
                    .lt("created_at", end_date.isoformat())
                    .execute()
                )

                # Group data by date in Python
                daily_data = self._group_by_date(result.data)
            else:
                daily_data = result.data

            # Get user's goal from user table
            user_result = (
                self.supabase.table("users")
                .select("daily_calorie_goal")
                .eq("id", user_id)
                .execute()
            )
            goal_calories = user_result.data[0]["daily_calorie_goal"] if user_result.data else None

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

            # Calculate summary statistics
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

            return DailyStatisticsResponse(
                data=data_points,
                period=period,
                summary=summary,
            )

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
        """Get macronutrient breakdown for a date range.

        Args:
            user_id: User identifier
            start_date: Start date (inclusive)
            end_date: End date (exclusive)

        Returns:
            Macronutrient breakdown response

        Raises:
            ValueError: If date range invalid
            Exception: If query fails
        """
        # Validate date range
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        if (end_date - start_date).days > 365:
            raise ValueError("Date range cannot exceed 365 days")

        try:
            # Query total macros for period
            result = (
                self.supabase.table("meals")
                .select("estimated_calories, estimated_protein, estimated_fat, estimated_carbs")
                .eq("user_id", user_id)
                .gte("created_at", start_date.isoformat())
                .lt("created_at", end_date.isoformat())
                .execute()
            )

            # Calculate totals
            total_protein = sum(float(m.get("estimated_protein", 0)) for m in result.data)
            total_fat = sum(float(m.get("estimated_fat", 0)) for m in result.data)
            total_carbs = sum(float(m.get("estimated_carbs", 0)) for m in result.data)
            total_calories = sum(float(m.get("estimated_calories", 0)) for m in result.data)

            # Calculate percentages (macros to calories conversion)
            # Protein: 4 kcal/g, Fat: 9 kcal/g, Carbs: 4 kcal/g
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
                    "total_meals": len(result.data),
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
        """Group meals by date and aggregate nutrition data.

        Args:
            meals: List of meal records

        Returns:
            List of daily aggregates
        """
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
            meal_date = meal["created_at"][:10]  # Extract YYYY-MM-DD
            daily_data[meal_date]["total_calories"] += float(meal.get("estimated_calories", 0))
            daily_data[meal_date]["total_protein"] += float(meal.get("estimated_protein", 0))
            daily_data[meal_date]["total_fat"] += float(meal.get("estimated_fat", 0))
            daily_data[meal_date]["total_carbs"] += float(meal.get("estimated_carbs", 0))
            daily_data[meal_date]["meal_count"] += 1

        # Convert to list format
        return [
            {
                "meal_date": meal_date,
                **data,
            }
            for meal_date, data in sorted(daily_data.items())
        ]


# Global service instance
_statistics_service: StatisticsService | None = None


def get_statistics_service() -> StatisticsService:
    """Get the global statistics service instance."""
    global _statistics_service
    if _statistics_service is None:
        _statistics_service = StatisticsService()
    return _statistics_service
