"""Tests for inline telemetry helpers in monitoring module."""

import pytest

from calorie_track_ai_bot.services import monitoring


@pytest.fixture(autouse=True)
def reset_inline_telemetry(monkeypatch):
    monkeypatch.setattr(monitoring, "_inline_telemetry", monitoring.InlineTelemetry(window=50))


def test_record_inline_ack_and_result_latency():
    monitoring.record_inline_ack_latency("inline_query", 1200)
    monitoring.record_inline_ack_latency("inline_query", 1800)
    monitoring.record_inline_result_latency("inline_query", 9500)

    snapshot = monitoring.get_inline_metrics_snapshot("inline_query")
    assert snapshot.sample_size == 2
    assert snapshot.ack_p95_ms >= 1800
    assert snapshot.result_p95_ms >= 9500
    assert snapshot.failure_reasons == {}


def test_record_inline_accuracy_delta():
    monitoring.record_inline_accuracy_delta("reply_mention", 2.5)
    monitoring.record_inline_accuracy_delta("reply_mention", 4.5)

    snapshot = monitoring.get_inline_metrics_snapshot("reply_mention")
    assert pytest.approx(snapshot.avg_accuracy_delta_pct, rel=1e-3) == 3.5
    assert snapshot.failure_reasons == {}


def test_record_permission_blocks_by_chat():
    monitoring.record_inline_permission_block_event("inline_query", "group")
    monitoring.record_inline_permission_block_event("inline_query", "group")
    monitoring.record_inline_permission_block_event("inline_query", "private")

    trigger_snapshot = monitoring.get_inline_metrics_snapshot("inline_query")
    assert trigger_snapshot.permission_blocks == 3
    assert trigger_snapshot.permission_blocks_by_chat["group"] == 2
    assert trigger_snapshot.permission_blocks_by_chat["private"] == 1

    overall_snapshot = monitoring.get_inline_metrics_snapshot()
    assert overall_snapshot.permission_blocks == 3
    assert overall_snapshot.failure_reasons == {}


def test_record_inline_failure_event():
    monitoring.record_inline_failure_event("inline_query", "processing_error")
    snapshot = monitoring.get_inline_metrics_snapshot("inline_query")
    assert snapshot.failure_reasons["processing_error"] == 1
