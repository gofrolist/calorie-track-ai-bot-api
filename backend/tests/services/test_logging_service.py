"""Tests for structured logging service enhancements."""

from unittest.mock import MagicMock

import pytest

from calorie_track_ai_bot.schemas import LogLevel
from calorie_track_ai_bot.services.logging_service import StructuredLoggingService


@pytest.mark.asyncio
async def test_create_log_entry_includes_inline_tags(monkeypatch):
    service = StructuredLoggingService()
    mock_logger = MagicMock()
    monkeypatch.setattr("calorie_track_ai_bot.services.logging_service.logger", mock_logger)

    entry = await service.create_log_entry(
        level=LogLevel.INFO,
        message="Inline telemetry context",
        inline_trigger="inline_query",
        inline_stage="analysis_started",
    )

    assert entry.context["inline_trigger"] == "inline_query"
    assert entry.context["inline_stage"] == "analysis_started"

    mock_logger.info.assert_called_once()
    extra = mock_logger.info.call_args.kwargs["extra"]
    assert extra["inline_trigger"] == "inline_query"
    assert extra["inline_stage"] == "analysis_started"
