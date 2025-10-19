"""Inline group flow integration tests."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app
from calorie_track_ai_bot.schemas import InlineTriggerType


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _group_reply_payload(text: str) -> dict:
    return {
        "update_id": 777001,
        "message": {
            "message_id": 710,
            "message_thread_id": 9001,
            "date": 1711111111,
            "chat": {
                "id": -100123456789,
                "type": "supergroup",
                "title": "Calorie Squad",
            },
            "from": {
                "id": 654321,
                "is_bot": False,
                "first_name": "Analyst",
                "username": "group_analyst",
            },
            "text": text,
            "entities": [
                {
                    "type": "mention",
                    "offset": 0,
                    "length": 18,
                }
            ],
            "reply_to_message": {
                "message_id": 501,
                "date": 1711110000,
                "chat": {
                    "id": -100123456789,
                    "type": "supergroup",
                },
                "from": {
                    "id": 112233,
                    "is_bot": False,
                    "first_name": "Chef",
                },
                "photo": [
                    {
                        "file_id": "benchmark-photo-id",
                        "file_unique_id": "unique-benchmark",
                        "file_size": 3072,
                        "width": 1024,
                        "height": 768,
                    }
                ],
            },
        },
    }


class TestInlineGroupFlow:
    """Inline group reply flow expectations."""

    def test_reply_flow_enqueues_job_and_sends_placeholder(self, client: TestClient) -> None:
        """Reply mentions should enqueue inline jobs and emit threaded placeholder messages."""
        payload = _group_reply_payload("@CalorieTrackAI_bot analyse this")

        with (
            patch(
                "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job", create=True
            ) as mock_enqueue,
            patch(
                "calorie_track_ai_bot.services.telegram.send_group_inline_placeholder",
                create=True,
            ) as mock_placeholder,
        ):
            mock_enqueue.return_value = "job-inline-reply-flow"

            response = client.post("/bot", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["job_id"] == "job-inline-reply-flow"
        assert body["trigger_type"] == "reply_mention"

        mock_enqueue.assert_called_once()
        _, enqueue_kwargs = mock_enqueue.call_args
        assert enqueue_kwargs["trigger_type"] == InlineTriggerType.reply_mention
        assert enqueue_kwargs["reply_to_message_id"] == 501
        assert enqueue_kwargs["thread_id"] == 9001
        assert enqueue_kwargs["raw_chat_id"] == -100123456789

        mock_placeholder.assert_called_once()
        placeholder_kwargs = mock_placeholder.call_args.kwargs
        assert placeholder_kwargs["chat_id"] == -100123456789
        assert placeholder_kwargs["thread_id"] == 9001
        assert placeholder_kwargs["reply_to_message_id"] == 501
        assert placeholder_kwargs["job_id"] == "job-inline-reply-flow"
        assert placeholder_kwargs["trigger_type"] == InlineTriggerType.reply_mention
