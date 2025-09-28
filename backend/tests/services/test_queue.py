"""Tests for queue module."""

import json
from unittest.mock import Mock, patch

import pytest

from calorie_track_ai_bot.services.queue import (
    QUEUE,
    dequeue_estimate_job,
    enqueue_estimate_job,
)


class TestQueueFunctions:
    """Test queue functions."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        with patch("calorie_track_ai_bot.services.queue.r") as mock_r:
            # Create a mock that can be configured per test
            mock_r.lpush = Mock()
            mock_r.brpop = Mock()
            yield mock_r

    @pytest.mark.asyncio
    async def test_enqueue_estimate_job(self, mock_redis):
        """Test enqueuing an estimate job."""
        photo_id = "photo123"

        async def mock_lpush(queue, data):
            return 1

        mock_redis.lpush.side_effect = mock_lpush

        result = await enqueue_estimate_job(photo_id)

        # Should return the photo_id
        assert result == photo_id

        # Should call lpush with correct parameters
        mock_redis.lpush.assert_called_once()
        call_args = mock_redis.lpush.call_args

        assert call_args[0][0] == QUEUE
        job_data = json.loads(call_args[0][1])
        assert job_data["photo_id"] == photo_id

    @pytest.mark.asyncio
    async def test_enqueue_estimate_job_with_uuid(self, mock_redis):
        """Test enqueuing an estimate job with UUID photo_id."""
        photo_id = "550e8400-e29b-41d4-a716-446655440000"

        async def mock_lpush(queue, data):
            return 1

        mock_redis.lpush.side_effect = mock_lpush

        result = await enqueue_estimate_job(photo_id)

        # Should return the photo_id
        assert result == photo_id

        # Should call lpush with correct parameters
        call_args = mock_redis.lpush.call_args
        job_data = json.loads(call_args[0][1])
        assert job_data["photo_id"] == photo_id

    @pytest.mark.asyncio
    async def test_dequeue_estimate_job_with_data(self, mock_redis):
        """Test dequeuing an estimate job when data is available."""
        job_data = {"photo_id": "photo456"}

        async def mock_brpop(queue, timeout):
            return ("estimate_jobs", json.dumps(job_data))

        mock_redis.brpop.side_effect = mock_brpop

        result = await dequeue_estimate_job()

        # Should return the parsed job data
        assert result == job_data

        # Should call brpop with correct parameters
        mock_redis.brpop.assert_called_once_with([QUEUE], timeout=10)

    @pytest.mark.asyncio
    async def test_dequeue_estimate_job_no_data(self, mock_redis):
        """Test dequeuing an estimate job when no data is available."""

        async def mock_brpop(queue, timeout):
            return None

        mock_redis.brpop.side_effect = mock_brpop

        result = await dequeue_estimate_job()

        # Should return None
        assert result is None

        # Should call brpop with correct parameters
        mock_redis.brpop.assert_called_once_with([QUEUE], timeout=10)

    @pytest.mark.asyncio
    async def test_dequeue_estimate_job_empty_list(self, mock_redis):
        """Test dequeuing an estimate job when brpop returns empty list."""

        async def mock_brpop(queue, timeout):
            return []

        mock_redis.brpop.side_effect = mock_brpop

        result = await dequeue_estimate_job()

        # Should return None (empty list means no data)
        assert result is None

    @pytest.mark.asyncio
    async def test_dequeue_estimate_job_invalid_json(self, mock_redis):
        """Test dequeuing an estimate job with invalid JSON."""

        async def mock_brpop(queue, timeout):
            return ("estimate_jobs", "invalid json")

        mock_redis.brpop.side_effect = mock_brpop

        # Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            await dequeue_estimate_job()

    @pytest.mark.asyncio
    async def test_dequeue_estimate_job_redis_error(self, mock_redis):
        """Test dequeuing an estimate job when Redis raises an error."""
        mock_redis.brpop.side_effect = Exception("Redis connection error")

        # Should propagate the exception
        with pytest.raises(Exception, match="Redis connection error"):
            await dequeue_estimate_job()

    @pytest.mark.asyncio
    async def test_enqueue_estimate_job_redis_error(self, mock_redis):
        """Test enqueuing an estimate job when Redis raises an error."""
        mock_redis.lpush.side_effect = Exception("Redis connection error")

        # Should propagate the exception
        with pytest.raises(Exception, match="Redis connection error"):
            await enqueue_estimate_job("photo123")

    def test_queue_constant(self):
        """Test that QUEUE constant is set correctly."""
        assert QUEUE == "estimate_jobs"

    @pytest.mark.asyncio
    async def test_job_data_structure(self, mock_redis):
        """Test that job data has the correct structure."""
        photo_id = "test_photo_123"

        async def mock_lpush(queue, data):
            return 1

        mock_redis.lpush.side_effect = mock_lpush

        await enqueue_estimate_job(photo_id)

        # Get the job data that was enqueued
        call_args = mock_redis.lpush.call_args
        job_data = json.loads(call_args[0][1])

        # Should have photo_id field
        assert "photo_id" in job_data
        assert job_data["photo_id"] == photo_id

        # Should be a valid JSON structure
        assert isinstance(job_data, dict)
        assert len(job_data) == 1  # Only photo_id field

    @pytest.mark.asyncio
    async def test_round_trip_job_processing(self, mock_redis):
        """Test complete round trip of job enqueue/dequeue."""
        photo_id = "roundtrip_photo_456"

        async def mock_lpush(queue, data):
            return 1

        mock_redis.lpush.side_effect = mock_lpush

        # Enqueue a job
        await enqueue_estimate_job(photo_id)

        # Get the job data that was enqueued
        enqueue_call_args = mock_redis.lpush.call_args
        job_data = json.loads(enqueue_call_args[0][1])

        # Mock the dequeue to return this same data
        async def mock_brpop(queue, timeout):
            return ("estimate_jobs", json.dumps(job_data))

        mock_redis.brpop.side_effect = mock_brpop

        # Dequeue the job
        result = await dequeue_estimate_job()

        # Should get back the same data
        assert result == job_data
        assert result["photo_id"] == photo_id
