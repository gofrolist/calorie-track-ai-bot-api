"""Integration tests for inline analysis flows (group, private, failure)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app
from calorie_track_ai_bot.schemas import InlineChatType, InlineTriggerType


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _group_reply_payload(
    text: str,
    *,
    file_id: str = "benchmark-photo-id",
    update_id: int = 777001,
    chat_id: int = -100123456789,
    chat_title: str = "Calorie Squad",
    from_id: int = 654321,
    from_name: str = "Analyst",
    from_username: str = "group_analyst",
    reply_from_id: int = 112233,
    reply_from_name: str = "Chef",
    reply_message_id: int = 501,
    thread_id: int = 9001,
) -> dict:
    """Build a group reply payload with a photo in the replied-to message."""
    return {
        "update_id": update_id,
        "message": {
            "message_id": 710,
            "message_thread_id": thread_id,
            "date": 1711111111,
            "chat": {
                "id": chat_id,
                "type": "supergroup",
                "title": chat_title,
            },
            "from": {
                "id": from_id,
                "is_bot": False,
                "first_name": from_name,
                "username": from_username,
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
                "message_id": reply_message_id,
                "date": 1711110000,
                "chat": {
                    "id": chat_id,
                    "type": "supergroup",
                },
                "from": {
                    "id": reply_from_id,
                    "is_bot": False,
                    "first_name": reply_from_name,
                },
                "photo": [
                    {
                        "file_id": file_id,
                        "file_unique_id": f"unique-{file_id}",
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


class TestPrivateInlineFlow:
    """Verify private inline queries propagate privacy context."""

    def test_private_inline_query_sets_privacy_metadata(self, client: TestClient) -> None:
        payload = {
            "update_id": 880001,
            "inline_query": {
                "id": "INLINE-PVT-1",
                "from": {
                    "id": 11111,
                    "is_bot": False,
                    "first_name": "Private",
                    "username": "private_user",
                },
                "query": '{"file_id": "pvt-file-1"}',
                "chat_type": "private",
            },
        }

        with (
            patch(
                "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job",
                create=True,
            ) as mock_enqueue,
            patch(
                "calorie_track_ai_bot.api.v1.bot.send_inline_query_acknowledgement",
                create=True,
            ) as mock_ack,
        ):
            mock_enqueue.return_value = "job-private-inline"

            response = client.post("/bot", json=payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["job_id"] == "job-private-inline"

        mock_enqueue.assert_called_once()
        _, enqueue_kwargs = mock_enqueue.call_args
        assert enqueue_kwargs["trigger_type"] == InlineTriggerType.inline_query
        assert enqueue_kwargs["chat_type"] == InlineChatType.private
        assert enqueue_kwargs["metadata"]["privacy_notice"] is True
        assert enqueue_kwargs["consent_scope"] == "inline_private"

        mock_ack.assert_called_once()
        placeholder_text = mock_ack.call_args.kwargs["placeholder_text"]
        assert "Privacy notice" in placeholder_text
        assert "View the inline usage guide" in placeholder_text


class TestInlineFailureFlow:
    """Validate inline reply handling enqueues job with failure metadata."""

    def test_group_failure_triggers_dm_fallback_and_telemetry(self, client: TestClient) -> None:
        payload = _group_reply_payload(
            "@CalorieTrackAI_bot fail this please",
            file_id="file-failure-1",
            update_id=910001,
            chat_id=-100500600,
            chat_title="Inline Failure Squad",
            from_id=443322,
            from_name="Failure",
            from_username="failure_hunter",
            reply_from_id=777888,
            reply_from_name="Photographer",
            reply_message_id=123,
            thread_id=55,
        )

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
