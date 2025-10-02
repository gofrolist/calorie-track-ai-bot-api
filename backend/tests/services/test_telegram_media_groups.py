"""
Tests for Telegram media group detection and photo aggregation
Feature: 003-update-logic-for
Task: T012
"""

from datetime import datetime
from unittest.mock import Mock

import pytest


class TestMediaGroupDetection:
    """Test bot's ability to detect and handle media groups from Telegram"""

    @pytest.mark.asyncio
    async def test_detect_media_group_id(self):
        """Should detect media_group_id from Telegram update"""
        from calorie_track_ai_bot.services.telegram import TelegramService

        service = TelegramService()

        # Mock Telegram update with media_group_id
        update = Mock()
        update.message.media_group_id = "12345678901234567"
        update.message.photo = [Mock()]  # Array of photo sizes

        media_group_id = await service.get_media_group_id(update)

        assert media_group_id == "12345678901234567"

    @pytest.mark.asyncio
    async def test_no_media_group_id_for_single_photo(self):
        """Should return None for single photo without media group"""
        from calorie_track_ai_bot.services.telegram import TelegramService

        service = TelegramService()

        update = Mock()
        update.message.media_group_id = None
        update.message.photo = [Mock()]

        media_group_id = await service.get_media_group_id(update)

        assert media_group_id is None

    @pytest.mark.asyncio
    async def test_aggregate_photos_by_media_group(self):
        """Should aggregate multiple photos with same media_group_id"""
        from calorie_track_ai_bot.services.telegram import TelegramService

        service = TelegramService()
        media_group_id = "test_group_123"

        # Simulate 3 photos arriving with same media_group_id
        photo_updates = [
            Mock(message_id=1, photo=[Mock()], media_group_id=media_group_id),
            Mock(message_id=2, photo=[Mock()], media_group_id=media_group_id),
            Mock(message_id=3, photo=[Mock()], media_group_id=media_group_id),
        ]

        # Test aggregation logic
        photos = await service.aggregate_media_group_photos(
            media_group_id, photo_updates, wait_ms=200
        )

        assert len(photos) == 3
        assert all(p.media_group_id == media_group_id for p in photos)

    @pytest.mark.asyncio
    async def test_extract_caption_from_first_photo(self):
        """Should extract caption/text from first photo in media group"""
        from calorie_track_ai_bot.services.telegram import TelegramService

        service = TelegramService()

        # First photo has caption
        updates = [
            Mock(message_id=1, caption="Chicken pasta dinner", media_group_id="group123"),
            Mock(message_id=2, caption=None, media_group_id="group123"),
            Mock(message_id=3, caption=None, media_group_id="group123"),
        ]

        caption = await service.extract_media_group_caption(updates)

        assert caption == "Chicken pasta dinner"

    @pytest.mark.asyncio
    async def test_wait_for_media_group_completion(self):
        """Should wait up to 200ms for all photos in media group"""
        from calorie_track_ai_bot.services.telegram import TelegramService

        service = TelegramService()

        # Simulate photos arriving over time
        start_time = datetime.now()

        # This should timeout after 200ms since no photos are added
        is_complete = await service.wait_for_media_group_complete(
            media_group_id="test_group",
            expected_count=3,  # Expect 3 photos
            timeout_ms=200,
        )

        elapsed = (datetime.now() - start_time).total_seconds() * 1000

        # Should wait approximately the timeout duration
        assert elapsed >= 190  # Should wait at least 190ms
        assert elapsed <= 250  # Allow some tolerance
        # Should return None on timeout (no photos added to buffer)
        assert is_complete is None
