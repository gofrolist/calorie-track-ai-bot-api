from typing import Any

from .. import database
from ._base import resolve_user_id


async def db_get_daily_summary(
    date: str, telegram_user_id: str | None = None
) -> dict[str, Any] | None:
    """Get daily summary for a specific date."""
    pool = await database.get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                "SELECT kcal_total FROM meals WHERE meal_date = %s AND user_id = %s",
                (date, user_id),
            )
        else:
            cur = await conn.execute("SELECT kcal_total FROM meals WHERE meal_date = %s", (date,))
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    total_kcal = sum(meal.get("kcal_total", 0) for meal in meals)
    macro_totals = {"protein_g": 0, "fat_g": 0, "carbs_g": 0}

    return {
        "user_id": user_id,
        "date": date,
        "kcal_total": total_kcal,
        "macros_totals": macro_totals,
    }


async def db_get_summaries_by_date_range(
    start_date: str, end_date: str, telegram_user_id: str | None = None
) -> dict[str, dict[str, Any]]:
    """Get summaries for a date range in a single query."""
    pool = await database.get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                """SELECT meal_date, kcal_total FROM meals
                   WHERE meal_date >= %s AND meal_date <= %s AND user_id = %s""",
                (start_date, end_date, user_id),
            )
        else:
            cur = await conn.execute(
                "SELECT meal_date, kcal_total FROM meals WHERE meal_date >= %s AND meal_date <= %s",
                (start_date, end_date),
            )
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    summaries: dict[str, dict[str, Any]] = {}
    for meal in meals:
        d = str(meal["meal_date"])
        if d not in summaries:
            summaries[d] = {
                "user_id": user_id,
                "date": d,
                "kcal_total": 0,
                "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
            }
        summaries[d]["kcal_total"] += meal.get("kcal_total", 0)

    return summaries


async def db_get_today_data(date: str, telegram_user_id: str | None = None) -> dict[str, Any]:
    """Get all data needed for the Today page in a single query."""
    pool = await database.get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                "SELECT * FROM meals WHERE meal_date = %s AND user_id = %s",
                (date, user_id),
            )
        else:
            cur = await conn.execute("SELECT * FROM meals WHERE meal_date = %s", (date,))
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    daily_summary = {
        "user_id": user_id,
        "date": date,
        "kcal_total": sum(meal.get("kcal_total", 0) for meal in meals),
        "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
    }

    return {"meals": meals, "daily_summary": daily_summary}
