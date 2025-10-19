"""Integration tests for inline failure handling and DM fallback."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app
from calorie_track_ai_bot.schemas import InlineTriggerType
from calorie_track_ai_bot.workers.estimate_worker import handle_inline_interaction_job


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _group_reply_payload(file_id: str) -> dict:
    return {
        "update_id": 910001,
        "message": {
            "message_id": 200,
            "message_thread_id": 55,
            "date": 1715000000,
            "chat": {
                "id": -100500600,
                "type": "supergroup",
                "title": "Inline Failure Squad",
            },
            "from": {
                "id": 443322,
                "is_bot": False,
                "first_name": "Failure",
                "username": "failure_hunter",
            },
            "text": "@CalorieTrackAI_bot fail this please",
            "entities": [
                {
                    "type": "mention",
                    "offset": 0,
                    "length": 18,
                }
            ],
            "reply_to_message": {
                "message_id": 123,
                "date": 1714999990,
                "chat": {
                    "id": -100500600,
                    "type": "supergroup",
                },
                "from": {
                    "id": 777888,
                    "is_bot": False,
                    "first_name": "Photographer",
                },
                "photo": [
                    {
                        "file_id": file_id,
                        "file_unique_id": "inline-failure-photo",
                        "file_size": 4096,
                        "width": 800,
                        "height": 600,
                    }
                ],
            },
        },
    }


class TestInlineFailureFlow:
    """Validate inline failure guidance and permission fallback behaviour."""

    def test_group_failure_triggers_dm_fallback_and_telemetry(self, client: TestClient) -> None:
        payload = _group_reply_payload("file-failure-1")

        async def fake_enqueue_inline_job(**kwargs):
            job_uuid = kwargs["job_id"]
            job_dict = {
                "job_id": str(job_uuid),
                "trigger_type": kwargs["trigger_type"].value,
                "chat_type": kwargs["chat_type"].value,
                "chat_id": kwargs.get("raw_chat_id"),
                "chat_id_hash": f"hash-{kwargs.get('raw_chat_id')}",
                "thread_id": kwargs.get("thread_id"),
                "reply_to_message_id": kwargs.get("reply_to_message_id"),
                "inline_message_id": kwargs.get("inline_message_id"),
                "file_id": kwargs["file_id"],
                "origin_message_id": kwargs.get("origin_message_id"),
                "source_user_id": kwargs.get("raw_user_id"),
                "source_user_hash": f"hash-{kwargs.get('raw_user_id')}",
                "requested_at": datetime.now(UTC).isoformat(),
                "metadata": kwargs.get("metadata"),
                "consent": {
                    "granted": kwargs.get("consent_granted", True),
                    "scope": kwargs.get("consent_scope"),
                    "reference": kwargs.get("consent_reference"),
                    "captured_at": datetime.now(UTC).isoformat(),
                    "retention_hours": kwargs.get("retention_hours", 24),
                },
                "retention_policy": {
                    "expires_in_hours": kwargs.get("retention_hours", 24),
                },
            }

            await handle_inline_interaction_job(job_dict)
            return str(job_uuid)

        with (
            patch(
                "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job",
                create=True,
            ) as mock_enqueue,
            patch(
                "calorie_track_ai_bot.services.telegram.send_group_inline_placeholder",
                create=True,
            ) as mock_placeholder,
            patch(
                "calorie_track_ai_bot.services.telegram.send_group_inline_result",
                side_effect=Exception("FORBIDDEN: bot was blocked"),
                create=True,
            ) as mock_send_group,
            patch(
                "calorie_track_ai_bot.services.telegram.get_bot",
                create=True,
            ) as mock_get_bot,
            patch(
                "calorie_track_ai_bot.services.inline_notifications.permission_notice_due",
                new=AsyncMock(return_value=True),
            ) as mock_notice_due,
            patch(
                "calorie_track_ai_bot.services.inline_notifications.mark_permission_notice",
                new=AsyncMock(),
            ) as mock_mark_notice,
            patch(
                "calorie_track_ai_bot.services.monitoring.record_inline_permission_block_event",
                create=True,
            ) as mock_permission_metric,
        ):
            mock_enqueue.side_effect = fake_enqueue_inline_job

            mock_bot_instance = AsyncMock()
            mock_bot_instance.get_file.return_value = {"file_path": "photos/fake.jpg"}
            mock_bot_instance.download_file.return_value = b"fake"
            mock_bot_instance.answer_inline_query.return_value = None
            mock_bot_instance.edit_message_text.return_value = None
            mock_bot_instance.send_message.return_value = None
            mock_get_bot.return_value = mock_bot_instance

            response = client.post("/bot", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["job_id"] == "job-inline-failure"
        assert body["trigger_type"] == "reply_mention"

        mock_enqueue.assert_called_once()
        enqueue_kwargs = mock_enqueue.call_args.kwargs
        assert enqueue_kwargs["trigger_type"] == InlineTriggerType.reply_mention
        assert enqueue_kwargs["metadata"]["failure_dm_required"] is True

        mock_placeholder.assert_called_once()
        mock_send_group.assert_called()
        mock_notice_due.assert_awaited_once()
        mock_mark_notice.assert_awaited_once()
        mock_permission_metric.assert_called_once()
        mock_bot_instance.send_message.assert_awaited()
