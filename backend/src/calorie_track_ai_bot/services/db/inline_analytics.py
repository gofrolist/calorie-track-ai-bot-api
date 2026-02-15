import uuid
from datetime import UTC, date, datetime
from typing import Any

from psycopg.types.json import Json

from ...schemas import InlineAnalyticsDaily, InlineChatType
from .. import database


def _inline_defaults(date_value: date, chat_type: InlineChatType) -> InlineAnalyticsDaily:
    return InlineAnalyticsDaily(
        id=uuid.uuid4(),
        date=date_value,
        chat_type=chat_type,
        trigger_counts={},
        request_count=0,
        success_count=0,
        failure_count=0,
        permission_block_count=0,
        avg_ack_latency_ms=0,
        p95_result_latency_ms=0,
        accuracy_within_tolerance_pct=0.0,
        failure_reasons=[],
        last_updated_at=datetime.now(UTC),
    )


def _to_inline_daily_model(row: dict[str, Any]) -> InlineAnalyticsDaily:
    payload = {**row}
    payload.setdefault("trigger_counts", {})
    payload.setdefault("failure_reasons", [])
    payload.setdefault("permission_block_count", 0)
    payload.setdefault("request_count", 0)
    payload.setdefault("success_count", 0)
    payload.setdefault("failure_count", 0)
    payload.setdefault("avg_ack_latency_ms", 0)
    payload.setdefault("p95_result_latency_ms", 0)
    payload.setdefault("accuracy_within_tolerance_pct", 0.0)
    payload.setdefault("last_updated_at", datetime.now(UTC).isoformat())
    return InlineAnalyticsDaily(**payload)


def _inline_payload(daily: InlineAnalyticsDaily) -> dict[str, Any]:
    payload = daily.model_dump(mode="json")
    if payload.get("failure_reasons") is None:
        payload["failure_reasons"] = []
    if payload.get("trigger_counts") is None:
        payload["trigger_counts"] = {}
    return payload


async def db_upsert_inline_analytics(daily: InlineAnalyticsDaily) -> InlineAnalyticsDaily:
    pool = await database.get_pool()

    payload = _inline_payload(daily)

    # Wrap jsonb columns with Json()
    jsonb_keys = {"trigger_counts", "failure_reasons"}
    adapted_values = [
        Json(v) if k in jsonb_keys and v is not None else v for k, v in payload.items()
    ]

    columns = ", ".join(payload.keys())
    placeholders = ", ".join(["%s"] * len(payload))
    update_set = ", ".join(f"{k} = EXCLUDED.{k}" for k in payload if k not in ("id",))

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"""INSERT INTO inline_analytics_daily ({columns}) VALUES ({placeholders})
                ON CONFLICT (date, chat_type) DO UPDATE SET {update_set}
                RETURNING *""",  # type: ignore[arg-type]
            tuple(adapted_values),
        )
        row = await cur.fetchone()

    returned = dict(row) if row else payload
    return _to_inline_daily_model(returned)


async def db_fetch_inline_analytics(
    range_start: date, range_end: date, chat_type: str | None = None
) -> list[InlineAnalyticsDaily]:
    pool = await database.get_pool()

    async with pool.connection() as conn:
        if chat_type:
            cur = await conn.execute(
                """SELECT * FROM inline_analytics_daily
                   WHERE date >= %s AND date <= %s AND chat_type = %s
                   ORDER BY date""",
                (range_start, range_end, chat_type),
            )
        else:
            cur = await conn.execute(
                """SELECT * FROM inline_analytics_daily
                   WHERE date >= %s AND date <= %s
                   ORDER BY date""",
                (range_start, range_end),
            )
        rows = await cur.fetchall()

    return [_to_inline_daily_model(dict(row)) for row in rows]


async def db_increment_inline_permission_block(
    *, date_value: date, chat_type: InlineChatType, increment: int = 1
) -> InlineAnalyticsDaily:
    existing_rows = await db_fetch_inline_analytics(date_value, date_value, chat_type.value)
    if existing_rows:
        current = existing_rows[0]
    else:
        current = _inline_defaults(date_value, chat_type)

    updated = current.model_copy(
        update={
            "permission_block_count": current.permission_block_count + increment,
            "last_updated_at": datetime.now(UTC),
        }
    )

    return await db_upsert_inline_analytics(updated)
