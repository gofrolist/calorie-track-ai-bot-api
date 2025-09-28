import calendar
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from ...services.db import db_get_daily_summary, db_get_summaries_by_date_range, db_get_today_data

router = APIRouter()


@router.get("/daily-summary/{date}")
async def get_daily_summary(date: str, request: Request) -> dict[str, Any]:
    """Get daily summary for a specific date."""
    try:
        # Get user ID from x-user-id header
        telegram_user_id = request.headers.get("x-user-id")

        summary = await db_get_daily_summary(date, telegram_user_id)
        if summary is None:
            # Return empty summary if no meals found
            return {
                "user_id": telegram_user_id,
                "date": date,
                "kcal_total": 0,
                "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
            }
        return summary
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/weekly-summary")
async def get_weekly_summary(
    request: Request,
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
) -> list[dict[str, Any]]:
    """Get weekly summary starting from the given date."""
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=6)

        start_date_str = start_dt.strftime("%Y-%m-%d")
        end_date_str = end_dt.strftime("%Y-%m-%d")

        telegram_user_id = request.headers.get("x-user-id")

        # Get all meals for the week in a single query
        summaries_dict = await db_get_summaries_by_date_range(
            start_date_str, end_date_str, telegram_user_id
        )

        # Build the response array with all 7 days
        summaries = []
        for i in range(7):
            current_date = start_dt + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")

            if date_str in summaries_dict:
                summaries.append(summaries_dict[date_str])
            else:
                # Create empty summary for days with no meals
                summaries.append(
                    {
                        "user_id": telegram_user_id,
                        "date": date_str,
                        "kcal_total": 0,
                        "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
                    }
                )

        return summaries
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/monthly-summary")
async def get_monthly_summary(
    request: Request,
    year: int = Query(..., description="Year"),
    month: int = Query(..., description="Month (1-12)"),
):
    """Get monthly summary for the given year and month."""
    try:
        # Get number of days in the month
        days_in_month = calendar.monthrange(year, month)[1]

        start_date_str = f"{year}-{month:02d}-01"
        end_date_str = f"{year}-{month:02d}-{days_in_month:02d}"

        telegram_user_id = request.headers.get("x-user-id")

        # Get all meals for the month in a single query
        summaries_dict = await db_get_summaries_by_date_range(
            start_date_str, end_date_str, telegram_user_id
        )

        # Build the response array with all days of the month
        summaries = []
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"

            if date_str in summaries_dict:
                summaries.append(summaries_dict[date_str])
            else:
                # Create empty summary for days with no meals
                summaries.append(
                    {
                        "user_id": telegram_user_id,
                        "date": date_str,
                        "kcal_total": 0,
                        "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
                    }
                )

        return summaries
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@router.get("/today/{date}")
async def get_today_data(date: str, request: Request):
    """Get all data needed for the Today page (meals + daily summary) in a single request."""
    try:
        # Get user ID from x-user-id header
        telegram_user_id = request.headers.get("x-user-id")

        today_data = await db_get_today_data(date, telegram_user_id)
        return today_data
    except Exception as e:
        raise HTTPException(500, str(e)) from e
