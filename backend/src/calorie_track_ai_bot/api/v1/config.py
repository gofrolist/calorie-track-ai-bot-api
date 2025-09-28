"""
Configuration management endpoints for UI and system settings.
"""

import re
import threading
import uuid
from datetime import UTC, datetime
from urllib.parse import urlparse

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...schemas import (
    Environment,
    LanguageDetectionResponse,
    LanguageSource,
    Theme,
    ThemeDetectionResponse,
    ThemeSource,
    UIConfiguration,
    UIConfigurationUpdate,
)
from ...services.config import APP_ENV

router = APIRouter()

# Initialize structured logger
logger = structlog.get_logger(__name__)

# Security dependency
security = HTTPBearer(auto_error=False)
security_dependency = Security(security)

# Allowed feature flags with validation
ALLOWED_FEATURE_FLAGS = {
    "enableThemeDetection": bool,
    "enableLanguageDetection": bool,
    "enableSafeAreas": bool,
    "enableLogging": bool,
    "enableDebugLogging": bool,
    "enableErrorReporting": bool,
    "enableAnalytics": bool,
    "enablePerformanceMonitoring": bool,
}

# ISO 639-1 language codes for validation
ISO_639_1_CODES = {
    # Currently supporting English and Russian
    # Full ISO 639-1 validation can be re-enabled when more languages are added
    "en",
    "ru",
    # Future languages can be added here when needed:
    # "es", "fr", "de", "it", "pt", "zh", "ja", "ar", etc.
}

# Thread-safe locks for in-memory storage
# In production, replace with proper database/cache layer
_config_lock = threading.RLock()
_config_id_lock = threading.RLock()

# Mock data store for development - keyed by user_id
# In production, this would be replaced with database operations
_ui_configs: dict[str, UIConfiguration] = {}
_config_ids_by_user: dict[str, str] = {}


class ConfigurationService:
    """Service for managing UI configurations with proper persistence logic."""

    @staticmethod
    def _get_correlation_id(request: Request) -> str:
        """Extract correlation ID from request headers."""
        return (
            request.headers.get("x-correlation-id")
            or request.headers.get("x-request-id")
            or str(uuid.uuid4())
        )

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        """Validate and sanitize user ID to prevent injection."""
        if not user_id or not isinstance(user_id, str):
            raise ValueError("User ID must be a non-empty string")

        # Remove potentially dangerous characters
        sanitized = re.sub(r"[^\w\-_.]", "", user_id)

        if len(sanitized) < 3 or len(sanitized) > 64:
            raise ValueError("User ID must be between 3 and 64 characters")

        if not sanitized:
            raise ValueError("User ID contains only invalid characters")

        return sanitized

    @staticmethod
    def _validate_url(url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def _validate_language_code(language: str) -> bool:
        """Validate language code against ISO 639-1 standard."""
        if not language or not isinstance(language, str):
            return False

        # Handle language-region codes like "en-US"
        primary_language = language.split("-")[0].lower()
        return primary_language in ISO_639_1_CODES

    @staticmethod
    def _sanitize_feature_flags(features: dict | None) -> dict:
        """Sanitize and validate feature flags, removing unknown flags."""
        if not features:
            return {}

        sanitized = {}
        for key, value in features.items():
            if key in ALLOWED_FEATURE_FLAGS:
                expected_type = ALLOWED_FEATURE_FLAGS[key]
                if isinstance(value, expected_type):
                    sanitized[key] = value
                # Coerce boolean values
                elif expected_type is bool:
                    sanitized[key] = bool(value)

        return sanitized

    @staticmethod
    def _get_or_create_config_id(user_id: str) -> str:
        """Get existing config ID for user or create new stable one (thread-safe)."""
        with _config_id_lock:
            if user_id not in _config_ids_by_user:
                _config_ids_by_user[user_id] = str(uuid.uuid4())
            return _config_ids_by_user[user_id]

    @staticmethod
    def _get_config(user_id: str) -> UIConfiguration | None:
        """Get configuration for user (thread-safe)."""
        with _config_lock:
            return _ui_configs.get(user_id)

    @staticmethod
    def _store_config(user_id: str, config: UIConfiguration) -> None:
        """Store configuration for user (thread-safe)."""
        with _config_lock:
            _ui_configs[user_id] = config

    @staticmethod
    def _get_environment() -> Environment:
        """Get environment from configuration."""
        return Environment.production if APP_ENV == "production" else Environment.development

    @staticmethod
    def _get_api_base_url() -> str:
        """Get API base URL from environment configuration."""
        # In production, this would come from environment variables
        if APP_ENV == "production":
            return "https://calorie-track-ai-bot.fly.dev"
        return "http://localhost:8000"


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = security_dependency
) -> str:
    """
    Extract and validate user ID from authentication token.

    In production, this validates JWT tokens and extracts user information.
    For development, allows header-based authentication with validation.

    Args:
        request: FastAPI request object
        credentials: HTTP Bearer token credentials

    Returns:
        str: Validated and sanitized user ID

    Raises:
        HTTPException: 401 for authentication failures
    """
    # For development: allow header-based authentication
    if APP_ENV != "production":
        user_id = request.headers.get("x-user-id")
        if user_id:
            try:
                return ConfigurationService._validate_user_id(user_id)
            except ValueError as e:
                logger.warning(
                    "Invalid user ID in header",
                    error=str(e),
                    # Don't log the actual invalid user_id for privacy
                    has_user_id=bool(user_id),
                )
                raise HTTPException(status_code=401, detail="Invalid user ID format") from e

    # Check for authorization header (production and development)
    if credentials and credentials.credentials:
        token = credentials.credentials
        # In production, validate JWT:
        # try:
        #     payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        #     user_id = payload.get("user_id")
        #     if not user_id:
        #         raise HTTPException(401, "Invalid token: missing user_id")
        #     return ConfigurationService._validate_user_id(user_id)
        # except JWTError as e:
        #     logger.warning("JWT validation failed", error=str(e))
        #     raise HTTPException(401, "Invalid authentication token")

        # For development: create mock user from token hash
        if len(token) >= 8:
            mock_user = f"user_{hash(token) % 10000:04d}"
            return ConfigurationService._validate_user_id(mock_user)

    # In production, require authentication
    if APP_ENV == "production":
        logger.warning(
            "Authentication required but not provided",
            has_credentials=credentials is not None,
            endpoint=str(request.url),
        )
        raise HTTPException(status_code=401, detail="Authentication required")

    # For development: return validated default user
    return ConfigurationService._validate_user_id("dev_user_001")


@router.get("/config/ui", response_model=UIConfiguration)
async def get_ui_configuration(
    request: Request, user_id: str = Depends(get_current_user)
) -> UIConfiguration:
    """
    Get current UI configuration including safe areas, theme, and language settings.

    Args:
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        UIConfiguration: Current UI configuration for the user

    Raises:
        HTTPException: 404 if configuration not found, 500 for server errors
    """
    correlation_id = ConfigurationService._get_correlation_id(request)

    logger.info("UI configuration requested", user_id=user_id, correlation_id=correlation_id)

    try:
        # Get stable config ID for user
        config_id_str = ConfigurationService._get_or_create_config_id(user_id)
        config_id = uuid.UUID(config_id_str)

        # Check if user has existing configuration (thread-safe)
        existing_config = ConfigurationService._get_config(user_id)
        if existing_config:
            logger.info(
                "Returning existing UI configuration",
                # Hash user_id for privacy in logs
                user_id_hash=hash(user_id) % 10000,
                config_id=str(config_id),
                correlation_id=correlation_id,
            )
            return existing_config

        # Create default configuration for new user
        now = datetime.now(UTC)
        config = UIConfiguration(
            id=config_id,
            environment=ConfigurationService._get_environment(),
            api_base_url=ConfigurationService._get_api_base_url(),
            safe_area_top=44,  # Typical iPhone notch height
            safe_area_bottom=34,  # Typical iPhone home indicator
            safe_area_left=0,
            safe_area_right=0,
            theme=Theme.auto,
            theme_source=ThemeSource.telegram,
            language="en",
            language_source=LanguageSource.telegram,
            features={
                "enableThemeDetection": True,
                "enableLanguageDetection": True,
                "enableSafeAreas": True,
                "enableLogging": True,
            },
            created_at=now,
            updated_at=now,
        )

        # Store the default configuration (thread-safe)
        ConfigurationService._store_config(user_id, config)

        logger.info(
            "Created new default UI configuration",
            # Hash user_id for privacy in logs
            user_id_hash=hash(user_id) % 10000,
            config_id=str(config_id),
            correlation_id=correlation_id,
        )

        return config

    except Exception as e:
        logger.error(
            "Failed to retrieve UI configuration",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Failed to retrieve UI configuration",
                "correlation_id": correlation_id,
            },
        ) from e


@router.put("/config/ui", response_model=UIConfiguration)
async def update_ui_configuration(
    update_data: UIConfigurationUpdate, request: Request, user_id: str = Depends(get_current_user)
) -> UIConfiguration:
    """
    Update UI configuration settings (idempotent).

    Args:
        update_data: Configuration update payload
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        UIConfiguration: Updated configuration

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """
    correlation_id = ConfigurationService._get_correlation_id(request)

    logger.info(
        "UI configuration update requested",
        user_id=user_id,
        correlation_id=correlation_id,
        update_fields=list(update_data.model_dump(exclude_unset=True).keys()),
    )

    try:
        # Validate input data
        validation_errors = {}

        # Validate URL if provided
        if update_data.api_base_url and not ConfigurationService._validate_url(
            update_data.api_base_url
        ):
            validation_errors["api_base_url"] = "Invalid URL format"

        # Validate safe area values
        for field in ["safe_area_top", "safe_area_bottom", "safe_area_left", "safe_area_right"]:
            value = getattr(update_data, field)
            if value is not None and (value < 0 or value > 200):
                validation_errors[field] = "Safe area value must be between 0 and 200 pixels"

        # Validate language code if provided
        if update_data.language and not ConfigurationService._validate_language_code(
            update_data.language
        ):
            validation_errors["language"] = (
                f"Invalid language code: {update_data.language}. Must be ISO 639-1 format."
            )

        if validation_errors:
            logger.warning(
                "UI configuration validation failed",
                user_id=user_id,
                correlation_id=correlation_id,
                validation_errors=validation_errors,
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "validation_error",
                    "message": "Invalid configuration data",
                    "validation_errors": validation_errors,
                    "correlation_id": correlation_id,
                },
            )

        # Get stable config ID for user
        config_id_str = ConfigurationService._get_or_create_config_id(user_id)
        config_id = uuid.UUID(config_id_str)

        # Sanitize feature flags (remove unknown flags, coerce types)
        sanitized_features = ConfigurationService._sanitize_feature_flags(update_data.features)
        if update_data.features and sanitized_features != update_data.features:
            logger.info(
                "Feature flags sanitized",
                user_id_hash=hash(user_id) % 10000,
                original_count=len(update_data.features),
                sanitized_count=len(sanitized_features),
                correlation_id=correlation_id,
            )

        # Get existing configuration or create default (thread-safe)
        existing_config = ConfigurationService._get_config(user_id)
        now = datetime.now(UTC)

        if existing_config:
            # Update existing configuration (preserve created_at)
            updated_config = existing_config.model_copy(
                update={
                    k: v
                    for k, v in update_data.model_dump(exclude_unset=True).items()
                    if v is not None
                }
                | {"updated_at": now}
            )
        else:
            # Create new configuration with defaults + updates
            base_config = {
                "id": config_id,
                "environment": ConfigurationService._get_environment(),
                "api_base_url": ConfigurationService._get_api_base_url(),
                "safe_area_top": 44.0,
                "safe_area_bottom": 34.0,
                "safe_area_left": 0.0,
                "safe_area_right": 0.0,
                "theme": Theme.auto,
                "theme_source": ThemeSource.telegram,
                "language": "en",
                "language_source": LanguageSource.telegram,
                "features": sanitized_features
                or {
                    "enableThemeDetection": True,
                    "enableLanguageDetection": True,
                    "enableSafeAreas": True,
                    "enableLogging": True,
                },
                "created_at": now,
                "updated_at": now,
            }

            # Apply updates to base configuration
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if value is not None:
                    base_config[key] = value

            updated_config = UIConfiguration(**base_config)

        # Store the updated configuration (thread-safe)
        ConfigurationService._store_config(user_id, updated_config)

        logger.info(
            "UI configuration updated successfully",
            user_id=user_id,
            config_id=str(config_id),
            correlation_id=correlation_id,
            is_new_config=existing_config is None,
        )

        return updated_config

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise

    except Exception as e:
        logger.error(
            "Failed to update UI configuration",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "internal_server_error",
                "message": "Failed to update UI configuration",
                "correlation_id": correlation_id,
            },
        ) from e


@router.patch("/config/ui", response_model=UIConfiguration)
async def patch_ui_configuration(
    update_data: UIConfigurationUpdate, request: Request, user_id: str = Depends(get_current_user)
) -> UIConfiguration:
    """
    Partially update UI configuration settings.

    Args:
        update_data: Configuration update payload (partial)
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        UIConfiguration: Updated configuration

    Raises:
        HTTPException: 400 for validation errors, 404 if config not found, 500 for server errors
    """
    correlation_id = ConfigurationService._get_correlation_id(request)

    logger.info(
        "UI configuration patch requested",
        user_id=user_id,
        correlation_id=correlation_id,
        patch_fields=list(update_data.model_dump(exclude_unset=True).keys()),
    )

    # Check if user has existing configuration (thread-safe)
    existing_config = ConfigurationService._get_config(user_id)
    if not existing_config:
        logger.warning(
            "UI configuration not found for patch", user_id=user_id, correlation_id=correlation_id
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": "config_not_found",
                "message": "UI configuration not found. Use PUT to create initial configuration.",
                "correlation_id": correlation_id,
            },
        )

    # Use the same update logic as PUT for existing configurations
    return await update_ui_configuration(update_data, request, user_id)


@router.get("/config/theme", response_model=ThemeDetectionResponse)
async def detect_theme(
    request: Request, user_id: str = Depends(get_current_user)
) -> ThemeDetectionResponse:
    """
    Detect and return current theme settings based on context.

    Args:
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        ThemeDetectionResponse: Detected theme information

    Raises:
        HTTPException: 500 for detection errors
    """
    correlation_id = ConfigurationService._get_correlation_id(request)

    logger.info("Theme detection requested", user_id=user_id, correlation_id=correlation_id)

    try:
        # Extract theme information from request context

        # 1. Check Telegram WebApp color scheme from headers
        telegram_color_scheme = request.headers.get("x-telegram-color-scheme")
        # telegram_theme_params could be used for advanced theme customization
        # telegram_theme_params = request.headers.get("x-telegram-theme-params")

        # 2. Check system preferences from User-Agent or Accept headers
        user_agent = request.headers.get("user-agent", "").lower()
        system_prefers_dark = (
            "dark" in user_agent or request.headers.get("sec-ch-prefers-color-scheme") == "dark"
        )

        # 3. Apply detection logic
        detected_theme = Theme.light
        theme_source = ThemeSource.system

        if telegram_color_scheme:
            # Telegram WebApp provides explicit color scheme
            detected_theme = Theme.dark if telegram_color_scheme == "dark" else Theme.light
            theme_source = ThemeSource.telegram
        elif system_prefers_dark is not None:
            # Fall back to system preference
            detected_theme = Theme.dark if system_prefers_dark else Theme.light
            theme_source = ThemeSource.system
        else:
            # Default to auto-detection
            detected_theme = Theme.auto
            theme_source = ThemeSource.manual

        now = datetime.now(UTC)

        response = ThemeDetectionResponse(
            theme=detected_theme,
            theme_source=theme_source,
            telegram_color_scheme=telegram_color_scheme,
            system_prefers_dark=system_prefers_dark,
            detected_at=now,
        )

        logger.info(
            "Theme detection completed",
            user_id=user_id,
            correlation_id=correlation_id,
            detected_theme=detected_theme.value,
            theme_source=theme_source.value,
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to detect theme",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "theme_detection_error",
                "message": "Failed to detect theme",
                "correlation_id": correlation_id,
            },
        ) from e


@router.get("/config/language", response_model=LanguageDetectionResponse)
async def detect_language(
    request: Request, user_id: str = Depends(get_current_user)
) -> LanguageDetectionResponse:
    """
    Detect and return current language settings based on context.

    Args:
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        LanguageDetectionResponse: Detected language information

    Raises:
        HTTPException: 500 for detection errors
    """
    correlation_id = ConfigurationService._get_correlation_id(request)

    logger.info("Language detection requested", user_id=user_id, correlation_id=correlation_id)

    try:
        # Extract language information from request context

        # 1. Check Telegram user language from headers
        telegram_language_code = request.headers.get("x-telegram-language-code")
        # telegram_user_data could be used for additional user context
        # telegram_user_data = request.headers.get("x-telegram-user-data")

        # 2. Check browser Accept-Language header
        accept_language = request.headers.get("accept-language", "")
        browser_language = None
        if accept_language:
            # Parse Accept-Language header (e.g., "en-US,en;q=0.9,es;q=0.8")
            languages = accept_language.split(",")
            if languages:
                primary_language = languages[0].strip().split(";")[0]
                browser_language = primary_language

        # 3. Apply detection logic with priority: Telegram > Browser > Default
        # Currently supported languages
        supported_languages = ["en", "ru"]
        detected_language = "en"  # Default fallback
        language_source = LanguageSource.manual

        if telegram_language_code:
            # Telegram provides user language preference
            detected_language = telegram_language_code
            language_source = LanguageSource.telegram
        elif browser_language:
            # Fall back to browser language
            detected_language = browser_language.split("-")[0]  # Extract primary language
            language_source = LanguageSource.browser

        # Validate detected language is ISO 639-1 format and supported
        if (
            not detected_language.isalpha()
            or len(detected_language) < 2
            or detected_language not in supported_languages
        ):
            detected_language = "en"  # Safe fallback
            language_source = LanguageSource.manual

        now = datetime.now(UTC)

        response = LanguageDetectionResponse(
            language=detected_language,
            language_source=language_source,
            telegram_language_code=telegram_language_code,
            browser_language=browser_language,
            detected_at=now,
            supported_languages=supported_languages,
        )

        logger.info(
            "Language detection completed",
            user_id=user_id,
            correlation_id=correlation_id,
            detected_language=detected_language,
            language_source=language_source.value,
            telegram_language=telegram_language_code,
            browser_language=browser_language,
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to detect language",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "language_detection_error",
                "message": "Failed to detect language",
                "correlation_id": correlation_id,
            },
        ) from e
