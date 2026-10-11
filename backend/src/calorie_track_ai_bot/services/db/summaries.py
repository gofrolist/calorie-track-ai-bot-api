from typing import Any

from .. import database
from ._base import LOCAL_MEAL_DATE_SQL, resolve_user_id

# Meals whose local calendar day (in the given time zone) equals the given date.
_ON_LOCAL_DATE = f"{LOCAL_MEAL_DATE_SQL} = %s"


async def db_get_daily_summary(
    date: str, telegram_user_id: str | None = None, tz: str = "UTC"
) -> dict[str, Any] | None:
    """Get daily summary for a specific calendar date in ``tz``."""
    pool = await database.get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                f"SELECT kcal_total FROM meals WHERE {_ON_LOCAL_DATE} AND user_id = %s",  # type: ignore[arg-type]
                (tz, date, user_id),
            )
        else:
            cur = await conn.execute(
                f"SELECT kcal_total FROM meals WHERE {_ON_LOCAL_DATE}",  # type: ignore[arg-type]
                (tz, date),
            )
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
    start_date: str, end_date: str, telegram_user_id: str | None = None, tz: str = "UTC"
) -> dict[str, dict[str, Any]]:
    """Get summaries for an inclusive range of calendar dates in ``tz`` in a single query."""
    pool = await database.get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                f"""SELECT {LOCAL_MEAL_DATE_SQL} AS meal_date, kcal_total FROM meals
                   WHERE {LOCAL_MEAL_DATE_SQL} BETWEEN %s AND %s AND user_id = %s""",  # type: ignore[arg-type]
                (tz, tz, start_date, end_date, user_id),
            )
        else:
            cur = await conn.execute(
                f"""SELECT {LOCAL_MEAL_DATE_SQL} AS meal_date, kcal_total FROM meals
                   WHERE {LOCAL_MEAL_DATE_SQL} BETWEEN %s AND %s""",  # type: ignore[arg-type]
                (tz, tz, start_date, end_date),
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


async def db_get_today_data(
    date: str, telegram_user_id: str | None = None, tz: str = "UTC"
) -> dict[str, Any]:
    """Get all data needed for the Today page in a single query (``date`` is in ``tz``)."""
    pool = await database.get_pool()

    user_id = await resolve_user_id(telegram_user_id)

    async with pool.connection() as conn:
        if user_id:
            cur = await conn.execute(
                f"SELECT * FROM meals WHERE {_ON_LOCAL_DATE} AND user_id = %s",  # type: ignore[arg-type]
                (tz, date, user_id),
            )
        else:
            cur = await conn.execute(
                f"SELECT * FROM meals WHERE {_ON_LOCAL_DATE}",  # type: ignore[arg-type]
                (tz, date),
            )
        rows = await cur.fetchall()

    meals = [dict(r) for r in rows]
    daily_summary = {
        "user_id": user_id,
        "date": date,
        "kcal_total": sum(meal.get("kcal_total", 0) for meal in meals),
        "macros_totals": {"protein_g": 0, "fat_g": 0, "carbs_g": 0},
    }

    return {"meals": meals, "daily_summary": daily_summary}
