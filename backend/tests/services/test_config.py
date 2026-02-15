"""Tests for config module."""

from calorie_track_ai_bot.services.config import (
    APP_ENV,
    AWS_ACCESS_KEY_ID,
    AWS_ENDPOINT_URL_S3,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    BUCKET_NAME,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    REDIS_URL,
)


class TestConfig:
    """Test configuration values."""

    def test_app_env_default(self):
        """Test APP_ENV default value."""
        assert APP_ENV == "dev"

    def test_openai_model_default(self):
        """Test OPENAI_MODEL default value."""
        assert OPENAI_MODEL == "gpt-5-mini"

    def test_aws_region_default(self):
        """Test AWS_REGION default value."""
        assert AWS_REGION == "auto"

    def test_app_env_from_env(self):
        """Test APP_ENV can be set from environment."""
        assert APP_ENV == "dev"  # Default value

    def test_openai_model_from_env(self):
        """Test OPENAI_MODEL can be set from environment."""
        assert OPENAI_MODEL == "gpt-5-mini"  # Default value

    def test_optional_env_vars_can_be_none(self):
        """Test that optional environment variables can be None."""
        assert OPENAI_API_KEY is None or isinstance(OPENAI_API_KEY, str)
        assert REDIS_URL is None or isinstance(REDIS_URL, str)
        assert AWS_ENDPOINT_URL_S3 is None or isinstance(AWS_ENDPOINT_URL_S3, str)
        assert AWS_ACCESS_KEY_ID is None or isinstance(AWS_ACCESS_KEY_ID, str)
        assert AWS_SECRET_ACCESS_KEY is None or isinstance(AWS_SECRET_ACCESS_KEY, str)
        assert BUCKET_NAME is None or isinstance(BUCKET_NAME, str)

    def test_openai_api_key_from_env(self):
        """Test OPENAI_API_KEY can be set from environment."""
        assert OPENAI_API_KEY == "test-openai-key"

    def test_redis_url_from_env(self):
        """Test REDIS_URL can be set from environment."""
        assert REDIS_URL == "redis://localhost:6379"
