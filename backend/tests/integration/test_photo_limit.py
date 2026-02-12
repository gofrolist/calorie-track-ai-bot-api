"""Integration test for 5-photo limit enforcement (Scenario 3)."""

import pytest

from calorie_track_ai_bot.services.telegram import get_photo_limit_message, validate_photo_count


class TestPhotoLimitValidation:
    """Test validation function for photo count."""

    @pytest.mark.asyncio
    async def test_valid_counts_accepted(self):
        assert validate_photo_count(1) is None
        assert validate_photo_count(3) is None
        assert validate_photo_count(5) is None

    @pytest.mark.asyncio
    async def test_zero_photos_rejected(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_photo_count(0)
        assert exc_info.value.status_code == 400
        assert "at least one photo" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_over_limit_rejected(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            validate_photo_count(6)
        assert exc_info.value.status_code == 400
        assert "maximum 5 photos" in exc_info.value.detail.lower()

        with pytest.raises(HTTPException) as exc_info:
            validate_photo_count(10)
        assert exc_info.value.status_code == 400
        assert "maximum 5 photos" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_user_friendly_message(self):
        message = get_photo_limit_message()

        assert "5 photos" in message
        assert "maximum" in message.lower() or "max" in message.lower()
        assert len(message) > 20
