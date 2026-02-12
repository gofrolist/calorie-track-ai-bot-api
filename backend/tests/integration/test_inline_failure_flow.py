"""Integration tests for inline failure handling and DM fallback."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app
from calorie_track_ai_bot.schemas import InlineTriggerType


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
    """Validate inline reply handling enqueues job with failure metadata."""

    def test_group_failure_triggers_dm_fallback_and_telemetry(self, client: TestClient) -> None:
        payload = _group_reply_payload("file-failure-1")

        async def fake_enqueue_inline_job(**kwargs):
            return str(kwargs["job_id"])

        with (
            patch(
                "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job",
                create=True,
            ) as mock_enqueue,
            patch(
                "calorie_track_ai_bot.services.telegram.send_group_inline_placeholder",
                new=AsyncMock(),
            ) as mock_placeholder,
        ):
            mock_enqueue.side_effect = fake_enqueue_inline_job

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
