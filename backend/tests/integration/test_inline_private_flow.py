"""Integration tests for private inline analysis flow."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app
from calorie_track_ai_bot.schemas import InlineChatType, InlineTriggerType


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


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
