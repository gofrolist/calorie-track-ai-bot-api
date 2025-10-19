"""Helpers for managing inline permission notifications with Redis TTL."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import redis.asyncio as redis

from ..schemas import InlinePermissionNotification
from .config import APP_ENV, REDIS_URL, logger

INLINE_PERMISSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours
INLINE_PERMISSION_KEY_PREFIX = "inline:permission_notice"

redis_client: redis.Redis | None = None

if REDIS_URL is not None:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
elif APP_ENV == "dev":
    logger.warning("REDIS_URL is not configured; inline permission notifications will be disabled.")
else:
    raise ValueError("REDIS_URL must be set for inline permission notifications")


def _build_permission_key(chat_id_hash: str, user_hash: str) -> str:
    return f"{INLINE_PERMISSION_KEY_PREFIX}:{chat_id_hash}:{user_hash}"


def _ensure_hash(value: str | None, field_name: str) -> str:
    if not value:
        raise ValueError(f"{field_name} is required and must be hashed before storage.")
    return value


async def get_permission_notice(
    chat_id_hash: str, user_hash: str
) -> InlinePermissionNotification | None:
    """Retrieve the most recent permission notification for the chat/user combination."""
    if redis_client is None:
        raise RuntimeError("Redis configuration not available; inline notifications disabled.")

    chat_hash = _ensure_hash(chat_id_hash, "chat_id_hash")
    user_hash = _ensure_hash(user_hash, "source_user_hash")
    key = _build_permission_key(chat_hash, user_hash)

    data = await redis_client.get(key)  # type: ignore
    if not data:
        return None

    payload = json.loads(data)
    return InlinePermissionNotification(**payload)


async def mark_permission_notice(chat_id_hash: str, user_hash: str) -> InlinePermissionNotification:
    """Persist a permission notification marker with TTL to avoid duplicate DMs."""
    if redis_client is None:
        raise RuntimeError("Redis configuration not available; inline notifications disabled.")

    chat_hash = _ensure_hash(chat_id_hash, "chat_id_hash")
    user_hash = _ensure_hash(user_hash, "source_user_hash")
    key = _build_permission_key(chat_hash, user_hash)

    notice = InlinePermissionNotification(
        chat_id_hash=chat_hash,
        source_user_hash=user_hash,
        last_notified_at=datetime.now(UTC),
    )
    payload = json.dumps(notice.model_dump(mode="json"))
    await redis_client.set(key, payload, ex=INLINE_PERMISSION_TTL_SECONDS)  # type: ignore
    logger.debug(
        "Inline permission notification recorded",
        extra={"chat_id_hash": chat_hash, "source_user_hash": user_hash},
    )
    return notice


async def permission_notice_due(chat_id_hash: str, user_hash: str) -> bool:
    """Return True when we should send a permission notification for this chat/user."""
    existing = await get_permission_notice(chat_id_hash, user_hash)
    return existing is None


async def clear_permission_notice(chat_id_hash: str, user_hash: str) -> None:
    """Remove permission notification marker (typically for manual resets or tests)."""
    if redis_client is None:
        raise RuntimeError("Redis configuration not available; inline notifications disabled.")

    chat_hash = _ensure_hash(chat_id_hash, "chat_id_hash")
    user_hash = _ensure_hash(user_hash, "source_user_hash")
    key = _build_permission_key(chat_hash, user_hash)
    await redis_client.delete(key)  # type: ignore
