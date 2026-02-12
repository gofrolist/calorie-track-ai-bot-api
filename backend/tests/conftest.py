"""Shared test fixtures and configuration."""

import asyncio
import os
from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Set test environment variables at module level (before any imports)
test_env_vars = {
    "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
    "OPENAI_API_KEY": "test-openai-key",
    "REDIS_URL": "redis://localhost:6379",
    "AWS_ENDPOINT_URL_S3": "https://test.tigris.com",
    "AWS_ACCESS_KEY_ID": "test-access-key",
    "AWS_SECRET_ACCESS_KEY": "test-secret-key",
    "BUCKET_NAME": "test-bucket",
    "AWS_REGION": "auto",
    "APP_ENV": "dev",
}

# Set environment variables immediately
for key, value in test_env_vars.items():
    os.environ[key] = value

# Mock external services at module level to prevent import-time initialization
with (
    patch("boto3.Session") as mock_session,
    patch("redis.asyncio.from_url") as mock_redis,
    patch("openai.OpenAI") as mock_openai,
    patch("psycopg_pool.AsyncConnectionPool") as mock_pool_cls,
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

    mock_pool_instance = AsyncMock()
    mock_pool_cls.return_value = mock_pool_instance

# Also mock the Redis client at the service level
with patch("calorie_track_ai_bot.services.queue.r") as mock_queue_redis:
    mock_queue_redis.lpush = Mock()
    mock_queue_redis.brpop = Mock()


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    yield

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


# =============================================================================
# INTEGRATION TEST HELPERS
# =============================================================================


def _make_mock_conn():
    """Create a mock async connection with cursor support."""
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value=None)
    mock_cursor.fetchall = AsyncMock(return_value=[])
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    return mock_conn


def _make_mock_pool():
    """Create a mock async connection pool.

    pool.connection() is synchronous in psycopg_pool (returns an async context manager),
    so the pool itself must be a regular Mock, not AsyncMock.
    """
    mock_pool = Mock()
    mock_conn = _make_mock_conn()

    # Wire up: pool.connection() -> async context manager -> mock_conn
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    ctx.__aexit__ = AsyncMock(return_value=False)
    mock_pool.connection.return_value = ctx

    return mock_pool, mock_conn


@pytest.fixture
def mock_db_pool():
    """Mock database connection pool for testing."""
    mock_pool, mock_conn = _make_mock_pool()

    with patch(
        "calorie_track_ai_bot.services.database.get_pool", new_callable=AsyncMock
    ) as mock_get_pool:
        mock_get_pool.return_value = mock_pool
        # Also patch get_pool in db.py since it's imported there
        with patch(
            "calorie_track_ai_bot.services.db.get_pool", new_callable=AsyncMock
        ) as mock_db_get_pool:
            mock_db_get_pool.return_value = mock_pool
            yield mock_pool, mock_conn


@pytest.fixture
def mock_supabase_client():
    """Backward-compat alias: mock database pool for testing.

    Returns the pool and connection mock as a tuple.
    Tests that previously used mock_supabase_client should migrate to mock_db_pool.
    """
    mock_pool, mock_conn = _make_mock_pool()

    with patch(
        "calorie_track_ai_bot.services.database.get_pool", new_callable=AsyncMock
    ) as mock_get_pool:
        mock_get_pool.return_value = mock_pool
        with patch(
            "calorie_track_ai_bot.services.db.get_pool", new_callable=AsyncMock
        ) as mock_db_get_pool:
            mock_db_get_pool.return_value = mock_pool
            yield mock_pool, mock_conn


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    with patch("calorie_track_ai_bot.services.queue.r") as mock_redis:
        mock_redis.lpush = Mock(return_value=1)
        mock_redis.brpop = Mock(return_value=[b"test_queue", b'{"test": "data"}'])
        mock_redis.ping = Mock(return_value=True)
        mock_redis.get = Mock(return_value=None)
        mock_redis.set = Mock(return_value=True)
        mock_redis.delete = Mock(return_value=1)
        yield mock_redis


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("calorie_track_ai_bot.services.estimator.client") as mock_openai:
        mock_response = Mock()
        mock_response.choices = [
            Mock(
                message=Mock(
                    content='{"kcal_mean": 500, "kcal_min": 400, "kcal_max": 600, "confidence": 0.8, "items": [{"name": "test food", "kcal": 500}]}'
                )
            )
        ]
        mock_openai.chat.completions.create.return_value = mock_response
        yield mock_openai


@pytest.fixture
def mock_s3_client():
    """Mock S3/Tigris client for testing."""
    with patch("calorie_track_ai_bot.services.storage.s3_client") as mock_s3:
        mock_s3.generate_presigned_url.return_value = "https://test-upload-url.com"
        mock_s3.head_object.return_value = {"ContentLength": 1024}
        mock_s3.put_object.return_value = {"ETag": "test-etag"}
        mock_s3.delete_object.return_value = {"DeleteMarker": True}
        yield mock_s3


@pytest.fixture
def mock_telegram_bot():
    """Mock Telegram bot for testing."""
    with patch("calorie_track_ai_bot.services.telegram.get_bot") as mock_get_bot:
        mock_bot = Mock()
        mock_bot.set_webhook = Mock(return_value=True)
        mock_bot.get_me = Mock(return_value=Mock(username="test_bot"))
        mock_bot.send_message = Mock(return_value=Mock(message_id=123))
        mock_bot.close = Mock()
        mock_get_bot.return_value = mock_bot
        yield mock_bot


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "telegram_id": 123456789,
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "language_code": "en",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def test_photo_data():
    """Sample photo data for testing."""
    return {
        "id": "photo-123",
        "user_id": "test-user-123",
        "file_id": "telegram-file-123",
        "file_path": "photos/test.jpg",
        "file_size": 1024,
        "width": 800,
        "height": 600,
        "upload_url": "https://test-upload-url.com",
        "uploaded": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def test_estimate_data():
    """Sample estimate data for testing."""
    return {
        "id": "estimate-123",
        "user_id": "test-user-123",
        "photo_id": "photo-123",
        "status": "done",
        "kcal_mean": 500,
        "kcal_min": 400,
        "kcal_max": 600,
        "confidence": 0.8,
        "items": [
            {
                "name": "Test Food",
                "kcal": 500,
                "protein": 20,
                "carbs": 60,
                "fat": 15,
                "confidence": 0.8,
            }
        ],
        "created_at": "2024-01-01T00:00:00Z",
        "completed_at": "2024-01-01T00:05:00Z",
    }


@pytest.fixture
def test_meal_data():
    """Sample meal data for testing."""
    return {
        "id": "meal-123",
        "user_id": "test-user-123",
        "estimate_id": "estimate-123",
        "meal_type": "lunch",
        "date": "2024-01-01",
        "confirmed": True,
        "kcal_total": 500,
        "protein_total": 20,
        "carbs_total": 60,
        "fat_total": 15,
        "items": [{"name": "Test Food", "kcal": 500, "protein": 20, "carbs": 60, "fat": 15}],
        "created_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def test_ui_config_data():
    """Sample UI configuration data for testing."""
    return {
        "id": "config-123",
        "user_id": "test-user-123",
        "environment": "development",
        "api_base_url": "http://localhost:8000",
        "safe_area_top": 44,
        "safe_area_bottom": 34,
        "safe_area_left": 0,
        "safe_area_right": 0,
        "theme": "light",
        "theme_source": "auto",
        "language": "en",
        "language_source": "telegram",
        "features": {
            "enableDebugLogging": True,
            "enableErrorReporting": False,
            "enableAnalytics": False,
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def test_log_entry():
    """Sample log entry for testing."""
    return {
        "level": "INFO",
        "service": "test-service",
        "correlation_id": "test-correlation-123",
        "message": "Test log message",
        "timestamp": "2024-01-01T00:00:00Z",
        "context": {"test_key": "test_value", "user_id": "test-user-123"},
    }


# =============================================================================
# API TEST HELPERS
# =============================================================================


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient

    from calorie_track_ai_bot.main import app

    return TestClient(app)


@pytest.fixture
def authenticated_headers():
    """Headers for authenticated requests."""
    return {
        "authorization": "Bearer test-token",
        "x-user-id": "123456789",
        "x-correlation-id": "test-correlation-123",
        "content-type": "application/json",
    }


@pytest.fixture
def telegram_headers():
    """Headers simulating Telegram WebApp."""
    return {
        "x-telegram-color-scheme": "dark",
        "x-telegram-language-code": "en",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 Telegram",
        "content-type": "application/json",
    }


# =============================================================================
# DATABASE TEST HELPERS
# =============================================================================


@pytest.fixture
def db_transaction():
    """Database transaction that rolls back after test."""
    yield


@pytest.fixture
def populate_test_data(mock_db_pool, test_user_data, test_photo_data, test_estimate_data):
    """Populate database with test data."""
    _mock_pool, mock_conn = mock_db_pool
    mock_cursor = AsyncMock()
    mock_cursor.fetchone = AsyncMock(return_value=test_user_data)
    mock_cursor.fetchall = AsyncMock(return_value=[test_user_data])
    mock_conn.execute = AsyncMock(return_value=mock_cursor)
    yield


# =============================================================================
# PERFORMANCE TEST HELPERS
# =============================================================================


@pytest.fixture
def performance_monitor():
    """Performance monitor for testing."""
    from calorie_track_ai_bot.services.monitoring import PerformanceMonitor

    monitor = PerformanceMonitor(collection_interval=1.0)
    yield monitor


@pytest.fixture
def benchmark_context():
    """Context for performance benchmarking in tests."""
    from calorie_track_ai_bot.services.monitoring import performance_monitor

    def _benchmark(operation_name: str):
        return performance_monitor.benchmark_operation(operation_name)

    return _benchmark


# =============================================================================
# ERROR SIMULATION HELPERS
# =============================================================================


@pytest.fixture
def simulate_database_error(mock_db_pool):
    """Simulate database errors."""
    _mock_pool, mock_conn = mock_db_pool

    def _simulate_error(error_type: str = "connection_error"):
        if error_type == "connection_error":
            mock_conn.execute.side_effect = ConnectionError("Database connection failed")
        elif error_type == "timeout":
            mock_conn.execute.side_effect = TimeoutError("Database timeout")
        else:
            mock_conn.execute.side_effect = Exception(f"Database error: {error_type}")

    return _simulate_error


@pytest.fixture
def simulate_redis_error(mock_redis_client):
    """Simulate Redis errors."""

    def _simulate_error(error_type: str = "connection_error"):
        if error_type == "connection_error":
            mock_redis_client.ping.side_effect = ConnectionError("Redis connection failed")
        elif error_type == "timeout":
            mock_redis_client.brpop.side_effect = TimeoutError("Redis timeout")
        else:
            mock_redis_client.ping.side_effect = Exception(f"Redis error: {error_type}")

    return _simulate_error


@pytest.fixture
def simulate_openai_error(mock_openai_client):
    """Simulate OpenAI API errors."""

    def _simulate_error(error_type: str = "rate_limit"):
        if error_type == "rate_limit":
            mock_openai_client.chat.completions.create.side_effect = Exception(
                "Rate limit exceeded"
            )
        elif error_type == "invalid_api_key":
            mock_openai_client.chat.completions.create.side_effect = Exception("Invalid API key")
        else:
            mock_openai_client.chat.completions.create.side_effect = Exception(
                f"OpenAI error: {error_type}"
            )

    return _simulate_error


# =============================================================================
# ASYNC TEST HELPERS
# =============================================================================


@pytest.fixture
def async_mock():
    """Create async mock."""

    def _async_mock(*args, **kwargs):
        m = Mock(*args, **kwargs)

        async def async_side_effect(*args, **kwargs):
            return m.return_value

        m.side_effect = async_side_effect
        return m

    return _async_mock


# =============================================================================
# VALIDATION HELPERS
# =============================================================================


def assert_valid_response_structure(response_data: dict, required_fields: list):
    """Assert that response has required structure."""
    assert isinstance(response_data, dict), "Response should be a dictionary"

    for field in required_fields:
        assert field in response_data, f"Response missing required field: {field}"


def assert_valid_timestamp(timestamp: str):
    """Assert that timestamp is in valid ISO format."""
    from datetime import datetime

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"Invalid timestamp format: {timestamp}")


def assert_valid_uuid(uuid_str: str):
    """Assert that string is a valid UUID."""
    import uuid

    try:
        uuid.UUID(uuid_str)
    except ValueError:
        pytest.fail(f"Invalid UUID format: {uuid_str}")


# =============================================================================
# CLEANUP HELPERS
# =============================================================================


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test."""
    yield
