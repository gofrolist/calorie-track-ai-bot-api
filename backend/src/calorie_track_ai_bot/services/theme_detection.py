"""
Theme Detection Service

Service for detecting and managing theme preferences from various sources
including Telegram WebApp API, system preferences, and manual overrides.
"""

import logging
from datetime import UTC, datetime

from ..schemas import Theme, ThemeSource

logger = logging.getLogger(__name__)


class ThemeDetectionService:
    """Service for detecting and managing theme preferences."""

    def __init__(self):
        self._theme_cache: dict[str, dict] = {}
        self._default_theme = "light"
        self._default_source = ThemeSource.system

    async def detect_theme(
        self,
        telegram_color_scheme: str | None = None,
        system_prefers_dark: bool | None = None,
        manual_theme: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """
        Detect theme from various sources with priority order.

        Priority: Manual > Telegram > System > Default

        Args:
            telegram_color_scheme: Theme from Telegram WebApp API
            system_prefers_dark: System preference for dark mode
            manual_theme: Manually set theme override
            user_id: Optional user ID for user-specific theme

        Returns:
            Dict: Theme detection result with theme, source, and metadata
        """
        cache_key = user_id or "default"

        # Check cache first
        if cache_key in self._theme_cache:
            cached_result = self._theme_cache[cache_key]
            # Return cached result if it's recent (within 5 minutes)
            if (datetime.now(UTC) - cached_result["detected_at"]).seconds < 300:
                return cached_result

        # Determine theme based on priority
        theme = self._default_theme
        source = self._default_source
        automatic = True

        if manual_theme and manual_theme in [t.value for t in Theme]:
            # Manual override has highest priority
            theme = manual_theme
            source = ThemeSource.manual
            automatic = False
        elif telegram_color_scheme and telegram_color_scheme in [t.value for t in Theme]:
            # Telegram WebApp API
            theme = telegram_color_scheme
            source = ThemeSource.telegram
        elif system_prefers_dark is not None:
            # System preference
            theme = "dark" if system_prefers_dark else "light"
            source = ThemeSource.system
        else:
            # Default fallback
            theme = self._default_theme
            source = ThemeSource.system

        result = {
            "theme": theme,
            "theme_source": source.value,
            "telegram_color_scheme": telegram_color_scheme,
            "system_prefers_dark": system_prefers_dark,
            "automatic": automatic,
            "detected_at": datetime.now(UTC),
        }

        # Cache the result
        self._theme_cache[cache_key] = result

        logger.info(
            f"Theme detected for user {user_id or 'default'}: {theme} "
            f"(source: {source.value}, automatic: {automatic})"
        )

        return result

    async def get_theme(self, user_id: str | None = None) -> str:
        """
        Get current theme for a user.

        Args:
            user_id: Optional user ID for user-specific theme

        Returns:
            str: Current theme
        """
        cache_key = user_id or "default"

        if cache_key in self._theme_cache:
            return self._theme_cache[cache_key]["theme"]

        # Return default theme if no cached result
        return self._default_theme

    async def set_theme(
        self, theme: str, user_id: str | None = None, source: ThemeSource = ThemeSource.manual
    ) -> dict:
        """
        Set theme for a user.

        Args:
            theme: Theme to set
            user_id: Optional user ID for user-specific theme
            source: Source of the theme setting

        Returns:
            Dict: Updated theme information
        """
        if theme not in [t.value for t in Theme]:
            raise ValueError(f"Invalid theme: {theme}")

        cache_key = user_id or "default"

        result = {
            "theme": theme,
            "theme_source": source.value,
            "telegram_color_scheme": None,
            "system_prefers_dark": None,
            "automatic": False,
            "detected_at": datetime.now(UTC),
        }

        # Update cache
        self._theme_cache[cache_key] = result

        logger.info(f"Theme set for user {user_id or 'default'}: {theme} (source: {source.value})")

        return result

    def clear_cache(self, user_id: str | None = None) -> None:
        """
        Clear theme cache.

        Args:
            user_id: Optional user ID to clear specific user cache
        """
        if user_id:
            self._theme_cache.pop(user_id, None)
        else:
            self._theme_cache.clear()

        logger.info(f"Theme cache cleared for user {user_id or 'all'}")

    def get_supported_themes(self) -> list[str]:
        """
        Get list of supported themes.

        Returns:
            list[str]: List of supported theme values
        """
        return [theme.value for theme in Theme]

    def get_theme_sources(self) -> list[str]:
        """
        Get list of supported theme sources.

        Returns:
            list[str]: List of supported theme source values
        """
        return [source.value for source in ThemeSource]

    async def validate_theme(self, theme: str) -> bool:
        """
        Validate if a theme is supported.

        Args:
            theme: Theme to validate

        Returns:
            bool: True if theme is valid
        """
        return theme in self.get_supported_themes()

    async def get_theme_info(self, user_id: str | None = None) -> dict:
        """
        Get comprehensive theme information for a user.

        Args:
            user_id: Optional user ID for user-specific theme

        Returns:
            Dict: Complete theme information
        """
        cache_key = user_id or "default"

        if cache_key in self._theme_cache:
            result = self._theme_cache[cache_key].copy()
        else:
            result = {
                "theme": self._default_theme,
                "theme_source": self._default_source.value,
                "telegram_color_scheme": None,
                "system_prefers_dark": None,
                "automatic": True,
                "detected_at": datetime.now(UTC),
            }

        # Add additional metadata
        result.update(
            {
                "supported_themes": self.get_supported_themes(),
                "supported_sources": self.get_theme_sources(),
                "cache_key": cache_key,
            }
        )

        return result


# Global service instance
theme_detection_service = ThemeDetectionService()
