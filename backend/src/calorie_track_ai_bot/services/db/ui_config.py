from datetime import UTC, datetime
from typing import Any

from psycopg.types.json import Json

from ...schemas import UIConfiguration, UIConfigurationUpdate
from .. import database
from ..config import logger


async def db_get_ui_configuration(user_id: str) -> dict[str, Any] | None:
    """Get UI configuration for a user."""
    pool = await database.get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute("SELECT * FROM ui_configurations WHERE user_id = %s", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_create_ui_configuration(user_id: str, config: UIConfiguration) -> dict[str, Any]:
    """Create a new UI configuration for a user."""
    pool = await database.get_pool()

    config_data = {
        "id": str(config.id),
        "user_id": user_id,
        "environment": config.environment,
        "api_base_url": config.api_base_url,
        "safe_area_top": config.safe_area_top,
        "safe_area_bottom": config.safe_area_bottom,
        "safe_area_left": config.safe_area_left,
        "safe_area_right": config.safe_area_right,
        "theme": config.theme,
        "theme_source": config.theme_source,
        "language": config.language,
        "language_source": config.language_source,
        "features": Json(config.features) if config.features is not None else None,
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }

    columns = ", ".join(config_data.keys())
    placeholders = ", ".join(["%s"] * len(config_data))

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"INSERT INTO ui_configurations ({columns}) VALUES ({placeholders}) RETURNING *",  # type: ignore[arg-type]
            tuple(config_data.values()),
        )
        row = await cur.fetchone()
        return dict(row) if row else config_data


async def db_update_ui_configuration(
    user_id: str, config_id: str, updates: UIConfigurationUpdate
) -> dict[str, Any] | None:
    """Update an existing UI configuration."""
    pool = await database.get_pool()

    update_data: dict[str, Any] = updates.model_dump(exclude_unset=True)
    if "features" in update_data and update_data["features"] is not None:
        update_data["features"] = Json(update_data["features"])

    update_data["updated_at"] = datetime.now(UTC).isoformat()

    set_clauses = [f"{k} = %s" for k in update_data]
    values = [*list(update_data.values()), config_id, user_id]

    async with pool.connection() as conn:
        cur = await conn.execute(
            f"UPDATE ui_configurations SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s RETURNING *",  # type: ignore[arg-type]
            tuple(values),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def db_delete_ui_configuration(user_id: str, config_id: str) -> bool:
    """Delete a UI configuration."""
    pool = await database.get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute(
            "DELETE FROM ui_configurations WHERE id = %s AND user_id = %s RETURNING id",
            (config_id, user_id),
        )
        row = await cur.fetchone()
        return row is not None


async def db_get_ui_configurations_by_user(user_id: str) -> list[dict[str, Any]]:
    """Get all UI configurations for a user."""
    pool = await database.get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT * FROM ui_configurations WHERE user_id = %s ORDER BY updated_at DESC",
            (user_id,),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def db_cleanup_old_ui_configurations(user_id: str, keep_count: int = 5) -> int:
    """Clean up old UI configurations, keeping only the most recent ones."""
    all_configs = await db_get_ui_configurations_by_user(user_id)

    if len(all_configs) <= keep_count:
        return 0

    configs_to_delete = all_configs[keep_count:]
    delete_ids = [config["id"] for config in configs_to_delete]

    if not delete_ids:
        return 0

    pool = await database.get_pool()

    async with pool.connection() as conn:
        cur = await conn.execute(
            "DELETE FROM ui_configurations WHERE id = ANY(%s) AND user_id = %s RETURNING id",
            (delete_ids, user_id),
        )
        rows = await cur.fetchall()
        deleted_count = len(rows)

    logger.info(f"Cleaned up {deleted_count} old UI configurations for user {user_id}")
    return deleted_count
