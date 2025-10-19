"""Tests for inline permission notification helpers."""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from calorie_track_ai_bot.services import inline_notifications as module
from calorie_track_ai_bot.services.inline_notifications import INLINE_PERMISSION_TTL_SECONDS


@pytest.fixture(autouse=True)
def reset_redis_client():
    """Ensure redis_client is reset between tests."""
    original = module.redis_client
    yield
    module.redis_client = original


@pytest.fixture
def redis_client(monkeypatch):
    client = AsyncMock()
    monkeypatch.setattr(module, "redis_client", client)
    return client


@pytest.mark.asyncio
async def test_mark_permission_notice_sets_ttl(redis_client):
    redis_client.set = AsyncMock()

    notice = await module.mark_permission_notice("chat-hash", "user-hash")

    redis_client.set.assert_awaited_once()
    key, payload = redis_client.set.call_args[0][:2]
    assert key == module._build_permission_key("chat-hash", "user-hash")
    assert redis_client.set.call_args.kwargs["ex"] == INLINE_PERMISSION_TTL_SECONDS

    data = json.loads(payload)
    assert data["chat_id_hash"] == "chat-hash"
    assert data["source_user_hash"] == "user-hash"
    assert notice.chat_id_hash == "chat-hash"
    assert notice.source_user_hash == "user-hash"


@pytest.mark.asyncio
async def test_get_permission_notice_returns_payload(redis_client):
    payload = {
        "chat_id_hash": "chat-hash",
        "source_user_hash": "user-hash",
        "last_notified_at": datetime.now(UTC).isoformat(),
    }
    redis_client.get = AsyncMock(return_value=json.dumps(payload))

    notice = await module.get_permission_notice("chat-hash", "user-hash")

    assert notice is not None
    assert notice.chat_id_hash == "chat-hash"
    assert notice.source_user_hash == "user-hash"


@pytest.mark.asyncio
async def test_permission_notice_due(redis_client):
    redis_client.get = AsyncMock(return_value=None)
    assert await module.permission_notice_due("chat-hash", "user-hash") is True

    redis_client.get = AsyncMock(
        return_value=json.dumps(
            {
                "chat_id_hash": "chat-hash",
                "source_user_hash": "user-hash",
                "last_notified_at": datetime.now(UTC).isoformat(),
            }
        )
    )
    assert await module.permission_notice_due("chat-hash", "user-hash") is False


@pytest.mark.asyncio
async def test_clear_permission_notice(redis_client):
    redis_client.delete = AsyncMock()

    await module.clear_permission_notice("chat-hash", "user-hash")

    redis_client.delete.assert_awaited_once_with(
        module._build_permission_key("chat-hash", "user-hash")
    )


@pytest.mark.asyncio
async def test_requires_hashed_identifiers(redis_client):
    with pytest.raises(ValueError):
        await module.mark_permission_notice("", "user-hash")
    with pytest.raises(ValueError):
        await module.get_permission_notice("chat-hash", "")
    with pytest.raises(ValueError):
        await module.clear_permission_notice("chat-hash", None)  # type: ignore[arg-type]
