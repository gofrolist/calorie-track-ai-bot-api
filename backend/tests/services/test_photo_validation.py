"""
Tests for photo validation including 5-photo limit
Feature: 003-update-logic-for
Task: T014
"""

import pytest
from fastapi import HTTPException


class TestPhotoValidation:
    """Test photo upload validation rules"""

    def test_validate_photo_count_within_limit(self):
        """Should accept photo counts from 1 to 5"""
        from calorie_track_ai_bot.services.telegram import validate_photo_count

        for count in range(1, 6):
            # Should not raise exception
            validate_photo_count(count)

    def test_reject_more_than_5_photos(self):
        """Should reject more than 5 photos with clear error message"""
        from calorie_track_ai_bot.services.telegram import validate_photo_count

        with pytest.raises(HTTPException) as exc_info:
            validate_photo_count(6)

        assert exc_info.value.status_code == 400
        assert "Maximum 5 photos" in str(exc_info.value.detail)

    def test_reject_zero_photos(self):
        """Should reject requests with zero photos"""
        from calorie_track_ai_bot.services.telegram import validate_photo_count

        with pytest.raises(HTTPException) as exc_info:
            validate_photo_count(0)

        assert exc_info.value.status_code == 400

    def test_informational_message_for_limit_exceeded(self):
        """Should generate user-friendly message when limit exceeded"""
        from calorie_track_ai_bot.services.telegram import get_photo_limit_message

        message = get_photo_limit_message()

        assert "5 photos" in message
        assert "one message" in message
        assert "better calorie estimation" in message or "better estimate" in message

    def test_validate_photo_display_order(self):
        """Should validate display_order is between 0 and 4"""
        from calorie_track_ai_bot.services.telegram import validate_display_order

        # Valid orders
        for order in range(5):
            validate_display_order(order)

        # Invalid orders
        with pytest.raises(ValueError):
            validate_display_order(-1)

        with pytest.raises(ValueError):
            validate_display_order(5)

    def test_validate_photo_mime_type(self):
        """Should validate that photo has valid image mime type"""
        from calorie_track_ai_bot.services.telegram import validate_photo_mime_type

        # Valid mime types
        valid_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        for mime_type in valid_types:
            validate_photo_mime_type(mime_type)

        # Invalid mime types
        invalid_types = ["video/mp4", "application/pdf", "text/plain"]
        for mime_type in invalid_types:
            with pytest.raises(ValueError):
                validate_photo_mime_type(mime_type)

    def test_validate_photo_file_size(self):
        """Should validate photo doesn't exceed 20MB (Telegram limit)"""
        from calorie_track_ai_bot.services.telegram import validate_photo_file_size

        # Valid sizes
        validate_photo_file_size(1024)  # 1KB
        validate_photo_file_size(1024 * 1024 * 10)  # 10MB
        validate_photo_file_size(1024 * 1024 * 20)  # 20MB exactly

        # Exceeds limit
        with pytest.raises(ValueError) as exc_info:
            validate_photo_file_size(1024 * 1024 * 21)  # 21MB

        assert "20MB" in str(exc_info.value)
