"""
Configuration management endpoints for UI and system settings.
"""

import re
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
ISO_639_1_CODES = {"en", "ru"}

# In-memory storage for development (keyed by user_id)
_ui_configs: dict[str, UIConfiguration] = {}
_config_ids_by_user: dict[str, str] = {}


def _get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request headers."""
    return (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )


def _validate_user_id(user_id: str) -> str:
    """Validate and sanitize user ID to prevent injection."""
    if not user_id or not isinstance(user_id, str):
        raise ValueError("User ID must be a non-empty string")

    sanitized = re.sub(r"[^\w\-_.]", "", user_id)

    if len(sanitized) < 3 or len(sanitized) > 64:
        raise ValueError("User ID must be between 3 and 64 characters")

    if not sanitized:
        raise ValueError("User ID contains only invalid characters")

    return sanitized


def _validate_url(url: str) -> bool:
    """Validate URL format."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def _validate_language_code(language: str) -> bool:
    """Validate language code against ISO 639-1 standard."""
    if not language or not isinstance(language, str):
        return False
    primary_language = language.split("-")[0].lower()
    return primary_language in ISO_639_1_CODES


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
            elif expected_type is bool:
                sanitized[key] = bool(value)

    return sanitized


def _get_or_create_config_id(user_id: str) -> str:
    """Get existing config ID for user or create a new stable one."""
    if user_id not in _config_ids_by_user:
        _config_ids_by_user[user_id] = str(uuid.uuid4())
    return _config_ids_by_user[user_id]


def _get_config(user_id: str) -> UIConfiguration | None:
    """Get configuration for user."""
    return _ui_configs.get(user_id)


def _store_config(user_id: str, config: UIConfiguration) -> None:
    """Store configuration for user."""
    _ui_configs[user_id] = config


def _get_environment() -> Environment:
    """Get environment from configuration."""
    return Environment.production if APP_ENV == "production" else Environment.development


def _get_api_base_url() -> str:
    """Get API base URL from environment configuration."""
    if APP_ENV == "production":
        return "https://calorie-track-ai-bot.fly.dev"
    return "http://localhost:8000"


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials | None = security_dependency
) -> str:
    """
    Extract and validate user ID from request headers.

    Uses x-user-id header for Telegram-based authentication.
    Falls back to Bearer token for compatibility.

    Returns:
        str: Validated and sanitized user ID

    Raises:
        HTTPException: 401 for authentication failures
    """
    # Primary auth: x-user-id header (Telegram user ID)
    user_id = request.headers.get("x-user-id")
    if user_id:
        try:
            return _validate_user_id(user_id)
        except ValueError as e:
            logger.warning("Invalid user ID in header", error=str(e))
            raise HTTPException(status_code=401, detail="Invalid user ID format") from e

    # Fallback: Bearer token (extract a user identifier from the token)
    if credentials and credentials.credentials and len(credentials.credentials) >= 8:
        mock_user = f"user_{hash(credentials.credentials) % 10000:04d}"
        return _validate_user_id(mock_user)

    # In production, require authentication
    if APP_ENV == "production":
        logger.warning(
            "Authentication required but not provided",
            endpoint=str(request.url),
        )
        raise HTTPException(status_code=401, detail="Authentication required")

    # For development: return default user
    return _validate_user_id("dev_user_001")


@router.get("/config/ui", response_model=UIConfiguration)
async def get_ui_configuration(
    request: Request, user_id: str = Depends(get_current_user)
) -> UIConfiguration:
    """
    Get current UI configuration including safe areas, theme, and language settings.

    Returns:
        UIConfiguration: Current UI configuration for the user

    Raises:
        HTTPException: 500 for server errors
    """
    correlation_id = _get_correlation_id(request)

    logger.info("UI configuration requested", user_id=user_id, correlation_id=correlation_id)

    try:
        config_id_str = _get_or_create_config_id(user_id)
        config_id = uuid.UUID(config_id_str)

        existing_config = _get_config(user_id)
        if existing_config:
            return existing_config

        # Create default configuration for new user
        now = datetime.now(UTC)
        config = UIConfiguration(
            id=config_id,
            environment=_get_environment(),
            api_base_url=_get_api_base_url(),
            safe_area_top=44,
            safe_area_bottom=34,
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

        _store_config(user_id, config)

        logger.info(
            "Created new default UI configuration",
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

    Returns:
        UIConfiguration: Updated configuration

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """
    correlation_id = _get_correlation_id(request)

    logger.info(
        "UI configuration update requested",
        user_id=user_id,
        correlation_id=correlation_id,
        update_fields=list(update_data.model_dump(exclude_unset=True).keys()),
    )

    try:
        validation_errors = {}

        if update_data.api_base_url and not _validate_url(update_data.api_base_url):
            validation_errors["api_base_url"] = "Invalid URL format"

        for field in ["safe_area_top", "safe_area_bottom", "safe_area_left", "safe_area_right"]:
            value = getattr(update_data, field)
            if value is not None and (value < 0 or value > 200):
                validation_errors[field] = "Safe area value must be between 0 and 200 pixels"

        if update_data.language and not _validate_language_code(update_data.language):
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

        config_id_str = _get_or_create_config_id(user_id)
        config_id = uuid.UUID(config_id_str)

        sanitized_features = _sanitize_feature_flags(update_data.features)
        if update_data.features and sanitized_features != update_data.features:
            logger.info(
                "Feature flags sanitized",
                original_count=len(update_data.features),
                sanitized_count=len(sanitized_features),
                correlation_id=correlation_id,
            )

        existing_config = _get_config(user_id)
        now = datetime.now(UTC)

        if existing_config:
            updated_config = existing_config.model_copy(
                update={
                    k: v
                    for k, v in update_data.model_dump(exclude_unset=True).items()
                    if v is not None
                }
                | {"updated_at": now}
            )
        else:
            base_config = {
                "id": config_id,
                "environment": _get_environment(),
                "api_base_url": _get_api_base_url(),
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

            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                if value is not None:
                    base_config[key] = value

            updated_config = UIConfiguration(**base_config)

        _store_config(user_id, updated_config)

        logger.info(
            "UI configuration updated successfully",
            user_id=user_id,
            config_id=str(config_id),
            correlation_id=correlation_id,
        )

        return updated_config

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            "Failed to update UI configuration",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
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

    Returns:
        UIConfiguration: Updated configuration

    Raises:
        HTTPException: 400 for validation errors, 404 if config not found, 500 for server errors
    """
    correlation_id = _get_correlation_id(request)

    existing_config = _get_config(user_id)
    if not existing_config:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "config_not_found",
                "message": "UI configuration not found. Use PUT to create initial configuration.",
                "correlation_id": correlation_id,
            },
        )

    return await update_ui_configuration(update_data, request, user_id)


@router.get("/config/theme", response_model=ThemeDetectionResponse)
async def detect_theme(
    request: Request, user_id: str = Depends(get_current_user)
) -> ThemeDetectionResponse:
    """
    Detect and return current theme settings based on context.

    Returns:
        ThemeDetectionResponse: Detected theme information

    Raises:
        HTTPException: 500 for detection errors
    """
    correlation_id = _get_correlation_id(request)

    logger.info("Theme detection requested", user_id=user_id, correlation_id=correlation_id)

    try:
        telegram_color_scheme = request.headers.get("x-telegram-color-scheme")

        user_agent = request.headers.get("user-agent", "").lower()
        system_prefers_dark = (
            "dark" in user_agent or request.headers.get("sec-ch-prefers-color-scheme") == "dark"
        )

        detected_theme = Theme.light
        theme_source = ThemeSource.system

        if telegram_color_scheme:
            detected_theme = Theme.dark if telegram_color_scheme == "dark" else Theme.light
            theme_source = ThemeSource.telegram
        elif system_prefers_dark is not None:
            detected_theme = Theme.dark if system_prefers_dark else Theme.light
            theme_source = ThemeSource.system
        else:
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

    Returns:
        LanguageDetectionResponse: Detected language information

    Raises:
        HTTPException: 500 for detection errors
    """
    correlation_id = _get_correlation_id(request)

    logger.info("Language detection requested", user_id=user_id, correlation_id=correlation_id)

    try:
        telegram_language_code = request.headers.get("x-telegram-language-code")

        accept_language = request.headers.get("accept-language", "")
        browser_language = None
        if accept_language:
            languages = accept_language.split(",")
            if languages:
                primary_language = languages[0].strip().split(";")[0]
                browser_language = primary_language

        supported_languages = ["en", "ru"]
        detected_language = "en"
        language_source = LanguageSource.manual

        if telegram_language_code:
            detected_language = telegram_language_code
            language_source = LanguageSource.telegram
        elif browser_language:
            detected_language = browser_language.split("-")[0]
            language_source = LanguageSource.browser

        if (
            not detected_language.isalpha()
            or len(detected_language) < 2
            or detected_language not in supported_languages
        ):
            detected_language = "en"
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
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to detect language",
            user_id=user_id,
            correlation_id=correlation_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "language_detection_error",
                "message": "Failed to detect language",
                "correlation_id": correlation_id,
            },
        ) from e
