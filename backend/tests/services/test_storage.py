"""Tests for storage module."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from calorie_track_ai_bot.services.storage import purge_transient_media, tigris_presign_put


class TestStorageFunctions:
    """Test storage functions."""

    @pytest.fixture
    def mock_s3_client(self):
        """Mock S3 client."""
        with (
            patch("calorie_track_ai_bot.services.storage.s3") as mock_s3,
            patch("calorie_track_ai_bot.services.storage.BUCKET_NAME", "test-bucket"),
        ):
            mock_s3.generate_presigned_url.return_value = "https://presigned-url.example.com"
            yield mock_s3

    @pytest.mark.asyncio
    async def test_tigris_presign_put(self, mock_s3_client):
        """Test generating presigned URL for PUT operation."""
        content_type = "image/jpeg"

        result = await tigris_presign_put(content_type)

        # Should return tuple of (key, url)
        assert isinstance(result, tuple)
        assert len(result) == 2
        key, url = result

        # Key should be a string with photos/ prefix and .jpg suffix
        assert isinstance(key, str)
        assert key.startswith("photos/")
        assert key.endswith(".jpg")

        # URL should be the mocked presigned URL
        assert url == "https://presigned-url.example.com"

        # Should call generate_presigned_url with correct parameters
        mock_s3_client.generate_presigned_url.assert_called_once()
        call_args = mock_s3_client.generate_presigned_url.call_args

        assert call_args.kwargs["ClientMethod"] == "put_object"
        assert call_args.kwargs["ExpiresIn"] == 900
        assert call_args.kwargs["HttpMethod"] == "PUT"

        # Check Params
        params = call_args.kwargs["Params"]
        assert "Bucket" in params
        assert "Key" in params
        assert "ContentType" in params
        assert params["ContentType"] == content_type

    @pytest.mark.asyncio
    async def test_tigris_presign_put_different_content_types(self, mock_s3_client):
        """Test generating presigned URL with different content types."""
        test_cases = ["image/png", "image/webp", "image/gif", "application/octet-stream"]

        for content_type in test_cases:
            result = await tigris_presign_put(content_type)

            # Should return tuple
            assert isinstance(result, tuple)
            key, _url = result

            # Key should still end with .jpg regardless of content type
            assert key.endswith(".jpg")

            # Should call with correct content type
            call_args = mock_s3_client.generate_presigned_url.call_args
            params = call_args.kwargs["Params"]
            assert params["ContentType"] == content_type

    @pytest.mark.asyncio
    async def test_tigris_presign_put_key_format(self, mock_s3_client):
        """Test that generated keys have correct format."""
        content_type = "image/jpeg"

        # Call multiple times to test UUID generation
        keys = []
        for _ in range(5):
            result = await tigris_presign_put(content_type)
            key, _ = result
            keys.append(key)

        # All keys should be unique
        assert len(set(keys)) == 5

        # All keys should have correct format
        for key in keys:
            assert key.startswith("photos/")
            assert key.endswith(".jpg")

            # Extract UUID part
            uuid_part = key[7:-4]  # Remove "photos/" prefix and ".jpg" suffix

            # Should be a valid UUID
            try:
                uuid.UUID(uuid_part)
            except ValueError:
                pytest.fail(f"Generated key {key} does not contain valid UUID")

    @pytest.mark.asyncio
    async def test_tigris_presign_put_s3_error(self, mock_s3_client):
        """Test handling of S3 client errors."""
        mock_s3_client.generate_presigned_url.side_effect = Exception("S3 Error")

        # Should propagate the exception
        with pytest.raises(Exception, match="S3 Error"):
            await tigris_presign_put("image/jpeg")

    @pytest.mark.asyncio
    async def test_tigris_presign_put_empty_content_type(self, mock_s3_client):
        """Test generating presigned URL with empty content type."""
        content_type = ""

        result = await tigris_presign_put(content_type)

        # Should still work
        assert isinstance(result, tuple)
        key, url = result
        assert isinstance(key, str)
        assert isinstance(url, str)

        # Should call with empty content type
        call_args = mock_s3_client.generate_presigned_url.call_args
        params = call_args.kwargs["Params"]
        assert params["ContentType"] == ""

    @pytest.mark.asyncio
    async def test_tigris_presign_put_none_content_type(self, mock_s3_client):
        """Test generating presigned URL with None content type."""
        content_type = None

        result = await tigris_presign_put(content_type)

        # Should still work
        assert isinstance(result, tuple)
        key, url = result
        assert isinstance(key, str)
        assert isinstance(url, str)

        # Should call with None content type
        call_args = mock_s3_client.generate_presigned_url.call_args
        params = call_args.kwargs["Params"]
        assert params["ContentType"] is None

    def test_presigned_url_parameters(self, mock_s3_client):
        """Test that presigned URL is generated with correct parameters."""
        content_type = "image/jpeg"

        # Call the function
        import asyncio

        asyncio.run(tigris_presign_put(content_type))

        # Check the call arguments
        call_args = mock_s3_client.generate_presigned_url.call_args

        # Should have all required parameters
        assert "ClientMethod" in call_args.kwargs
        assert "Params" in call_args.kwargs
        assert "ExpiresIn" in call_args.kwargs
        assert "HttpMethod" in call_args.kwargs

        # Check parameter values
        assert call_args.kwargs["ClientMethod"] == "put_object"
        assert call_args.kwargs["ExpiresIn"] == 900  # 15 minutes
        assert call_args.kwargs["HttpMethod"] == "PUT"

        # Check Params structure
        params = call_args.kwargs["Params"]
        assert "Bucket" in params
        assert "Key" in params
        assert "ContentType" in params
        assert params["ContentType"] == content_type

    @pytest.mark.asyncio
    async def test_multiple_calls_different_keys(self, mock_s3_client):
        """Test that multiple calls generate different keys."""
        content_type = "image/jpeg"

        # Make multiple calls
        results = []
        for _ in range(3):
            result = await tigris_presign_put(content_type)
            results.append(result)

        # All results should be different
        keys = [result[0] for result in results]
        urls = [result[1] for result in results]

        # Keys should be unique
        assert len(set(keys)) == 3

        # URLs should be the same (mocked)
        assert len(set(urls)) == 1
        assert urls[0] == "https://presigned-url.example.com"

    @pytest.mark.asyncio
    async def test_tigris_presign_put_custom_prefix(self, mock_s3_client):
        """Inline uploads should support custom prefixes."""
        key, _ = await tigris_presign_put("image/jpeg", prefix="inline")
        assert key.startswith("inline/")

    def test_purge_transient_media_deletes_old_objects(self, mock_s3_client):
        """Purge routine should delete inline artifacts older than retention window."""
        old_time = datetime.now(UTC) - timedelta(hours=25)
        recent_time = datetime.now(UTC) - timedelta(hours=1)

        paginator = Mock()
        paginator.paginate.return_value = [
            {
                "Contents": [
                    {"Key": "inline/old-object.jpg", "LastModified": old_time},
                    {"Key": "inline/new-object.jpg", "LastModified": recent_time},
                ]
            }
        ]
        mock_s3_client.get_paginator.return_value = paginator
        mock_s3_client.delete_object = Mock()

        deleted = purge_transient_media(prefixes=["inline/"], retention_hours=24)

        assert deleted == {"inline/": ["inline/old-object.jpg"]}
        mock_s3_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="inline/old-object.jpg"
        )

    def test_purge_transient_media_no_deletions(self, mock_s3_client):
        """Purge routine should skip objects within retention window."""
        paginator = Mock()
        paginator.paginate.return_value = [{"Contents": []}]
        mock_s3_client.get_paginator.return_value = paginator
        mock_s3_client.delete_object = Mock()

        deleted = purge_transient_media(prefixes=["inline/"], retention_hours=24)

        assert deleted == {}
        mock_s3_client.delete_object.assert_not_called()

    def test_purge_transient_media_handles_naive_timestamps(self, mock_s3_client):
        """Purge routine should coerce naive datetimes to UTC before comparison."""
        old_time = (datetime.now(UTC) - timedelta(hours=30)).replace(tzinfo=None)
        paginator = Mock()
        paginator.paginate.return_value = [
            {"Contents": [{"Key": "inline/naive.jpg", "LastModified": old_time}]}
        ]
        mock_s3_client.get_paginator.return_value = paginator
        mock_s3_client.delete_object = Mock()

        deleted = purge_transient_media(prefixes=["inline/"], retention_hours=24)

        assert deleted == {"inline/": ["inline/naive.jpg"]}
        mock_s3_client.delete_object.assert_called_once()
