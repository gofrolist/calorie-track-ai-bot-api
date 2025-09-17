"""Shared test fixtures and configuration."""

import asyncio
import os
from collections.abc import Generator
from unittest.mock import Mock, patch

import pytest

# Set test environment variables at module level (before any imports)
test_env_vars = {
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_KEY": "test-supabase-key",
    "SUPABASE_SERVICE_ROLE_KEY": "test-supabase-service-role-key",
    "OPENAI_API_KEY": "test-openai-key",
    "REDIS_URL": "redis://localhost:6379",
    "AWS_ENDPOINT_URL_S3": "https://test.tigris.com",
    "AWS_ACCESS_KEY_ID": "test-access-key",
    "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    "BUCKET_NAME": "test-bucket",
    "AWS_REGION": "auto",
}

# Set environment variables immediately
for key, value in test_env_vars.items():
    os.environ[key] = value

# Mock external services at module level to prevent import-time initialization
with (
    patch("boto3.Session") as mock_session,
    patch("redis.asyncio.from_url") as mock_redis,
    patch("openai.OpenAI") as mock_openai,
    patch("supabase.create_client") as mock_supabase,
):
    # Configure mocks
    mock_s3_client = Mock()
    mock_s3_client.generate_presigned_url.return_value = "https://test-url.com"
    mock_session.return_value.client.return_value = mock_s3_client

    mock_redis_instance = Mock()
    mock_redis_instance.lpush = Mock()
    mock_redis_instance.brpop = Mock()
    mock_redis.return_value = mock_redis_instance

    mock_openai_instance = Mock()
    mock_openai_instance.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content='{"kcal_mean": 500, "kcal_min": 400, "kcal_max": 600, "confidence": 0.8, "items": []}'
                )
            )
        ]
    )
    mock_openai.return_value = mock_openai_instance

    mock_supabase_instance = Mock()
    mock_supabase_instance.table.return_value.insert.return_value.execute.return_value = Mock(
        data=[]
    )
    mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value = Mock(
        data=[]
    )
    mock_supabase.return_value = mock_supabase_instance

# Also mock the Redis client at the service level
with patch("calorie_track_ai_bot.services.queue.r") as mock_queue_redis:
    mock_queue_redis.lpush = Mock()
    mock_queue_redis.brpop = Mock()


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Environment variables are already set at module level
    yield

    # Clean up - remove test environment variables
    for key in test_env_vars.keys():
        if key in os.environ:
            del os.environ[key]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for anyio."""
    return "asyncio"
