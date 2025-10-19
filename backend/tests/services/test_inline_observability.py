"""Observability tests for inline telemetry and failure metrics."""

from unittest.mock import patch

import pytest

from calorie_track_ai_bot.services import monitoring


@pytest.fixture(autouse=True)
def reset_inline_metrics(monkeypatch):
    monkeypatch.setattr(monitoring, "_inline_telemetry", monitoring.InlineTelemetry(window=20))


def test_inline_failure_emits_telemetry_and_alert(monkeypatch):
    with patch("calorie_track_ai_bot.services.monitoring.logger") as mock_logger:
        monitoring.record_inline_permission_block_event("reply_mention", "group")
        monitoring.record_inline_result_latency("reply_mention", 15000)

    snapshot = monitoring.get_inline_metrics_snapshot("reply_mention")
    assert snapshot.permission_blocks == 1
    assert snapshot.permission_blocks_by_chat["group"] == 1
    assert snapshot.result_p95_ms >= 15000

    # verify alert logging executed
    warning_calls = [
        call for call in mock_logger.warning.call_args_list if "permission_block" in str(call)
    ]
    assert warning_calls, "Expected permission block warning to be logged"
