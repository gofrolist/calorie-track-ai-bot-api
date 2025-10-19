"""Contract tests for Telegram inline webhook handling."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app
from calorie_track_ai_bot.schemas import InlineChatType, InlineTriggerType


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestInlineWebhookContracts:
    """Inline webhook acknowledgement contracts."""

    def test_inline_query_acknowledgement_structure(self, client: TestClient) -> None:
        """Inline queries should return structured acknowledgement with job metadata."""
        inline_payload = {
            "update_id": 555001,
            "inline_query": {
                "id": "INLINE123",
                "from": {
                    "id": 987654,
                    "is_bot": False,
                    "first_name": "Group",
                    "username": "group_invoker",
                },
                "query": '{"file_id": "inline-file-123", "origin_message_id": "orig-321"}',
                "chat_type": "supergroup",
            },
        }

        with (
            patch(
                "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job", create=True
            ) as mock_enqueue,
            patch(
                "calorie_track_ai_bot.api.v1.bot.send_inline_query_acknowledgement", create=True
            ) as mock_ack,
        ):
            mock_enqueue.return_value = "job-inline-query-uuid"

            response = client.post("/bot", json=inline_payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["job_id"] == "job-inline-query-uuid"
        assert body["trigger_type"] == "inline_query"

        mock_enqueue.assert_called_once()
        _, kwargs = mock_enqueue.call_args
        assert kwargs["trigger_type"] == InlineTriggerType.inline_query
        # supergroup requests must be normalised to group analytics buckets
        assert kwargs["chat_type"] == InlineChatType.group
        assert kwargs["inline_message_id"] == "INLINE123"
        assert kwargs["raw_user_id"] == 987654
        assert kwargs["file_id"] == "inline-file-123"
        assert kwargs["origin_message_id"] == "orig-321"
        assert kwargs["raw_chat_id"] is None
        mock_ack.assert_called_once()

    def test_group_reply_inline_acknowledgement(self, client: TestClient) -> None:
        """Reply mentions in groups should enqueue inline jobs with reply metadata."""
        inline_reply_payload = {
            "update_id": 555002,
            "message": {
                "message_id": 84,
                "message_thread_id": 777,
                "date": 1710001111,
                "chat": {
                    "id": -100999888777,
                    "type": "supergroup",
                    "title": "Inline Testers",
                },
                "from": {
                    "id": 24680,
                    "is_bot": False,
                    "first_name": "Reply",
                    "username": "reply_captain",
                },
                "text": "@CalorieTrackAI_bot please analyse this",
                "entities": [
                    {
                        "type": "mention",
                        "offset": 0,
                        "length": 18,
                    }
                ],
                "reply_to_message": {
                    "message_id": 42,
                    "date": 1710000000,
                    "chat": {
                        "id": -100999888777,
                        "type": "supergroup",
                    },
                    "from": {
                        "id": 13579,
                        "is_bot": False,
                        "first_name": "Photographer",
                    },
                    "photo": [
                        {
                            "file_id": "abc123",
                            "file_unique_id": "unique-photo",
                            "file_size": 2048,
                            "width": 800,
                            "height": 600,
                        }
                    ],
                },
            },
        }

        with patch(
            "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job", create=True
        ) as mock_enqueue:
            mock_enqueue.return_value = "job-inline-reply-uuid"

            response = client.post("/bot", json=inline_reply_payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["job_id"] == "job-inline-reply-uuid"
        assert body["trigger_type"] == "reply_mention"

        mock_enqueue.assert_called_once()
        _, kwargs = mock_enqueue.call_args
        assert kwargs["trigger_type"] == InlineTriggerType.reply_mention
        assert kwargs["chat_type"] == InlineChatType.group
        assert kwargs["reply_to_message_id"] == 42
        assert kwargs["thread_id"] == 777
        assert kwargs["raw_chat_id"] == -100999888777
        assert kwargs["raw_user_id"] == 24680

    def test_private_inline_query_includes_disclaimer_placeholder(self, client: TestClient) -> None:
        """Private inline queries should include privacy disclaimers in placeholder results."""
        inline_payload = {
            "update_id": 555010,
            "inline_query": {
                "id": "INLINE999",
                "from": {
                    "id": 43210,
                    "is_bot": False,
                    "first_name": "Solo",
                    "username": "solo_user",
                },
                "query": '{"file_id": "private-file-777", "chat_id": 43210}',
                "chat_type": "private",
            },
        }

        with (
            patch(
                "calorie_track_ai_bot.api.v1.bot.enqueue_inline_job", create=True
            ) as mock_enqueue,
            patch(
                "calorie_track_ai_bot.api.v1.bot.send_inline_query_acknowledgement", create=True
            ) as mock_ack,
        ):
            mock_enqueue.return_value = "job-inline-private-uuid"

            response = client.post("/bot", json=inline_payload)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["job_id"] == "job-inline-private-uuid"
        assert body["trigger_type"] == "inline_query"

        mock_enqueue.assert_called_once()
        _, enqueue_kwargs = mock_enqueue.call_args
        assert enqueue_kwargs["trigger_type"] == InlineTriggerType.inline_query
        assert enqueue_kwargs["chat_type"] == InlineChatType.private
        assert enqueue_kwargs["file_id"] == "private-file-777"
        assert enqueue_kwargs["metadata"]["privacy_notice"] is True

        mock_ack.assert_called_once()
        ack_kwargs = mock_ack.call_args.kwargs
        assert ack_kwargs["trigger_type"] == InlineTriggerType.inline_query
        placeholder_text = ack_kwargs["placeholder_text"]
        assert "Privacy notice" in placeholder_text
        assert "We only retain anonymised aggregates" in placeholder_text
