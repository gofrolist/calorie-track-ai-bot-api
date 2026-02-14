import logging
import os
import uuid
from datetime import UTC, datetime

from ..schemas import UIConfiguration, UIConfigurationUpdate

APP_ENV: str = os.getenv("APP_ENV", "dev")

# Logging configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Set specific loggers
logger = logging.getLogger("calorie_track_ai_bot")
if LOG_LEVEL == "DEBUG":
    # Enable debug logging for all our modules when DEBUG level is set
    for module_name in ["calorie_track_ai_bot", "fastapi", "uvicorn"]:
        logging.getLogger(module_name).setLevel(logging.DEBUG)

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

REDIS_URL: str | None = os.getenv("REDIS_URL")

# Tigris S3-compatible storage configuration
# Using standard AWS S3 environment variables as per Fly.io Tigris documentation
AWS_ENDPOINT_URL_S3: str | None = os.getenv("AWS_ENDPOINT_URL_S3")
AWS_ACCESS_KEY_ID: str | None = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: str | None = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME: str | None = os.getenv("BUCKET_NAME")
AWS_REGION: str = os.getenv("AWS_REGION", "auto")

# Telegram Bot configuration
TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")

# Inline mode configuration
INLINE_MODE_ENABLED: bool = os.getenv("INLINE_MODE_ENABLED", "false").lower() == "true"
INLINE_HASH_SALT: str = os.getenv("INLINE_HASH_SALT", "")
INLINE_THROUGHPUT_PER_MIN: int = int(os.getenv("INLINE_THROUGHPUT_PER_MIN", "60"))
INLINE_BURST_RPS: int = int(os.getenv("INLINE_BURST_RPS", "5"))

# Performance testing configuration
THREAD_DELTA_LIMIT: int = int(os.getenv("THREAD_DELTA_LIMIT", "20"))
PERFORMANCE_THRESHOLD_FACTOR: float = float(os.getenv("PERFORMANCE_THRESHOLD_FACTOR", "1.0"))
HEALTH_TIME_LIMIT: float = float(os.getenv("HEALTH_TIME_LIMIT", "200"))
MEMORY_THRESHOLD_MB: float = float(os.getenv("MEMORY_THRESHOLD_MB", "100"))
CPU_THRESHOLD_PERCENT: float = float(os.getenv("CPU_THRESHOLD_PERCENT", "200"))
WEBHOOK_URL: str | None = os.getenv("WEBHOOK_URL")
USE_WEBHOOK: bool = os.getenv("USE_WEBHOOK", "false").lower() == "true"
ENABLE_WORKER: bool = os.getenv("ENABLE_WORKER", "false").lower() == "true"


# CORS configuration
def get_cors_origins() -> list[str]:
    """Get CORS origins based on environment."""
    cors_origins_env = os.getenv("CORS_ORIGINS", "")

    if cors_origins_env:
        # Parse comma-separated origins from environment variable
        origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
        return origins

    # Default origins based on environment
    if APP_ENV == "production":
        return [
            "https://calorie-track-ai-bot.vercel.app",
            "https://t.me",
        ]
    else:
        # Development environment - allow local development
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "https://localhost:3000",
            "https://127.0.0.1:3000",
        ]


def get_trusted_hosts() -> list[str]:
    """Get trusted hosts for production environment."""
    trusted_hosts_env = os.getenv("TRUSTED_HOSTS", "")

    if trusted_hosts_env:
        return [host.strip() for host in trusted_hosts_env.split(",") if host.strip()]

    # Default trusted hosts for production
    return ["calorie-track-ai-bot.fly.dev", "*.fly.dev", "localhost", "127.0.0.1"]


def get_app_env() -> str:
    """Get application environment."""
    return APP_ENV


class UIConfigurationService:
    """Service for managing UI configuration settings."""

    def __init__(self):
        self._config_cache: dict[str, UIConfiguration] = {}
        self._default_config = self._create_default_config()

    def _create_default_config(self) -> UIConfiguration:
        """Create default UI configuration."""
        # Map 'dev' to 'development' for schema compatibility
        env = get_app_env()
        if env == "dev":
            env = "development"
        elif env not in ["development", "production"]:
            env = "development"

        from ..schemas import Environment, LanguageSource, Theme, ThemeSource

        return UIConfiguration(
            id=uuid.uuid4(),
            environment=Environment(env),
            api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
            safe_area_top=0,
            safe_area_bottom=0,
            safe_area_left=0,
            safe_area_right=0,
            theme=Theme.auto,
            theme_source=ThemeSource.system,
            language="en",
            language_source=LanguageSource.browser,
            features={
                "enableDebugLogging": get_app_env() == "development",
                "enableErrorReporting": get_app_env() == "production",
                "enableAnalytics": get_app_env() == "production",
                "enableDevTools": get_app_env() == "development",
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def get_configuration(self, user_id: str | None = None) -> UIConfiguration:
        """
        Get UI configuration for a user.

        Args:
            user_id: Optional user ID for user-specific configuration

        Returns:
            UIConfiguration: UI configuration object
        """
        cache_key = user_id or "default"

        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        # For now, return default configuration
        # In production, this would fetch from database
        config = self._default_config.model_copy()
        self._config_cache[cache_key] = config

        return config

    async def update_configuration(
        self, config_update: UIConfigurationUpdate, user_id: str | None = None
    ) -> UIConfiguration:
        """
        Update UI configuration.

        Args:
            config_update: Configuration update data
            user_id: Optional user ID for user-specific configuration

        Returns:
            UIConfiguration: Updated UI configuration
        """
        current_config = await self.get_configuration(user_id)

        # Update configuration with provided values
        update_data = config_update.model_dump(exclude_unset=True)
        updated_config = current_config.model_copy(update=update_data)
        updated_config.updated_at = datetime.now(UTC)

        # Cache the updated configuration
        cache_key = user_id or "default"
        self._config_cache[cache_key] = updated_config

        # In production, this would save to database
        logger.info(f"UI configuration updated for user {user_id or 'default'}: {update_data}")

        return updated_config

    def clear_cache(self, user_id: str | None = None) -> None:
        """
        Clear configuration cache.

        Args:
            user_id: Optional user ID to clear specific user cache
        """
        if user_id:
            self._config_cache.pop(user_id, None)
        else:
            self._config_cache.clear()

        logger.info(f"Configuration cache cleared for user {user_id or 'all'}")

    def get_feature_flag(self, feature_name: str, user_id: str | None = None) -> bool:
        """
        Get feature flag value.

        Args:
            feature_name: Name of the feature flag
            user_id: Optional user ID for user-specific flags

        Returns:
            bool: Feature flag value
        """
        config = self._config_cache.get(user_id or "default", self._default_config)
        return config.features.get(feature_name, False) if config.features else False

    def set_feature_flag(self, feature_name: str, value: bool, user_id: str | None = None) -> None:
        """
        Set feature flag value.

        Args:
            feature_name: Name of the feature flag
            value: Feature flag value
            user_id: Optional user ID for user-specific flags
        """
        cache_key = user_id or "default"
        config = self._config_cache.get(cache_key, self._default_config)

        if config.features is None:
            config.features = {}

        config.features[feature_name] = value
        config.updated_at = datetime.now(UTC)

        self._config_cache[cache_key] = config

        logger.info(f"Feature flag '{feature_name}' set to {value} for user {user_id or 'default'}")


# Global service instance
ui_configuration_service = UIConfigurationService()
