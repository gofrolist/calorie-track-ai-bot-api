"""
Language Detection Service

Service for detecting and managing language preferences from various sources
including Telegram user data, browser preferences, and manual overrides.
"""

import logging
import re
from datetime import UTC, datetime

from ..schemas import LanguageSource

logger = logging.getLogger(__name__)


class LanguageDetectionService:
    """Service for detecting and managing language preferences."""

    def __init__(self):
        self._language_cache: dict[str, dict] = {}
        self._default_language = "en"
        self._default_source = LanguageSource.browser
        self._supported_languages = ["en", "ru"]  # As per user requirement

    async def detect_language(
        self,
        telegram_language: str | None = None,
        browser_language: str | None = None,
        manual_language: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """
        Detect language from various sources with priority order.

        Priority: Manual > Telegram > Browser > Default

        Args:
            telegram_language: Language from Telegram user data
            browser_language: Language from browser navigator
            manual_language: Manually set language override
            user_id: Optional user ID for user-specific language

        Returns:
            Dict: Language detection result with language, source, and metadata
        """
        cache_key = user_id or "default"

        # Check cache first
        if cache_key in self._language_cache:
            cached_result = self._language_cache[cache_key]
            # Return cached result if it's recent (within 5 minutes)
            if (datetime.now(UTC) - cached_result["detected_at"]).seconds < 300:
                return cached_result

        # Determine language based on priority
        language = self._default_language
        source = self._default_source
        automatic = True

        if manual_language and self._is_valid_language(manual_language):
            # Manual override has highest priority
            language = manual_language
            source = LanguageSource.manual
            automatic = False
        elif telegram_language and self._is_valid_language(telegram_language):
            # Telegram user data
            language = telegram_language
            source = LanguageSource.telegram
        elif browser_language and self._is_valid_language(browser_language):
            # Browser navigator
            language = browser_language
            source = LanguageSource.browser
        else:
            # Default fallback
            language = self._default_language
            source = LanguageSource.browser

        result = {
            "language": language,
            "language_source": source.value,
            "telegram_language": telegram_language,
            "browser_language": browser_language,
            "supported_languages": self._supported_languages.copy(),
            "automatic": automatic,
            "detected_at": datetime.now(UTC),
        }

        # Cache the result
        self._language_cache[cache_key] = result

        logger.info(
            f"Language detected for user {user_id or 'default'}: {language} "
            f"(source: {source.value}, automatic: {automatic})"
        )

        return result

    async def get_language(self, user_id: str | None = None) -> str:
        """
        Get current language for a user.

        Args:
            user_id: Optional user ID for user-specific language

        Returns:
            str: Current language code
        """
        cache_key = user_id or "default"

        if cache_key in self._language_cache:
            return self._language_cache[cache_key]["language"]

        # Return default language if no cached result
        return self._default_language

    async def set_language(
        self,
        language: str,
        user_id: str | None = None,
        source: LanguageSource = LanguageSource.manual,
    ) -> dict:
        """
        Set language for a user.

        Args:
            language: Language code to set
            user_id: Optional user ID for user-specific language
            source: Source of the language setting

        Returns:
            Dict: Updated language information
        """
        if not self._is_valid_language(language):
            raise ValueError(f"Invalid or unsupported language: {language}")

        cache_key = user_id or "default"

        result = {
            "language": language,
            "language_source": source.value,
            "telegram_language": None,
            "browser_language": None,
            "supported_languages": self._supported_languages.copy(),
            "automatic": False,
            "detected_at": datetime.now(UTC),
        }

        # Update cache
        self._language_cache[cache_key] = result

        logger.info(
            f"Language set for user {user_id or 'default'}: {language} (source: {source.value})"
        )

        return result

    def clear_cache(self, user_id: str | None = None) -> None:
        """
        Clear language cache.

        Args:
            user_id: Optional user ID to clear specific user cache
        """
        if user_id:
            self._language_cache.pop(user_id, None)
        else:
            self._language_cache.clear()

        logger.info(f"Language cache cleared for user {user_id or 'all'}")

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported languages.

        Returns:
            List[str]: List of supported language codes
        """
        return self._supported_languages.copy()

    def get_language_sources(self) -> list[str]:
        """
        Get list of supported language sources.

        Returns:
            List[str]: List of supported language source values
        """
        return [source.value for source in LanguageSource]

    def _is_valid_language(self, language: str) -> bool:
        """
        Validate if a language code is valid and supported.

        Args:
            language: Language code to validate

        Returns:
            bool: True if language is valid and supported
        """
        if not language:
            return False

        # Check if it's a valid ISO 639-1 language code format
        if not re.match(r"^[a-z]{2}(-[A-Z]{2})?$", language):
            return False

        # Extract primary language code (e.g., 'en' from 'en-US')
        primary_language = language.split("-")[0]

        # Check if it's in our supported languages
        return primary_language in self._supported_languages

    async def validate_language(self, language: str) -> bool:
        """
        Validate if a language is supported.

        Args:
            language: Language code to validate

        Returns:
            bool: True if language is valid and supported
        """
        return self._is_valid_language(language)

    async def get_language_info(self, user_id: str | None = None) -> dict:
        """
        Get comprehensive language information for a user.

        Args:
            user_id: Optional user ID for user-specific language

        Returns:
            Dict: Complete language information
        """
        cache_key = user_id or "default"

        if cache_key in self._language_cache:
            result = self._language_cache[cache_key].copy()
        else:
            result = {
                "language": self._default_language,
                "language_source": self._default_source.value,
                "telegram_language": None,
                "browser_language": None,
                "supported_languages": self._supported_languages.copy(),
                "automatic": True,
                "detected_at": datetime.now(UTC),
            }

        # Add additional metadata
        result.update(
            {
                "supported_sources": self.get_language_sources(),
                "cache_key": cache_key,
            }
        )

        return result

    async def add_supported_language(self, language: str) -> bool:
        """
        Add a new supported language.

        Args:
            language: Language code to add

        Returns:
            bool: True if language was added successfully
        """
        if not re.match(r"^[a-z]{2}(-[A-Z]{2})?$", language):
            logger.warning(f"Invalid language code format: {language}")
            return False

        primary_language = language.split("-")[0]

        if primary_language not in self._supported_languages:
            self._supported_languages.append(primary_language)
            logger.info(f"Added supported language: {primary_language}")
            return True

        return False

    async def remove_supported_language(self, language: str) -> bool:
        """
        Remove a supported language.

        Args:
            language: Language code to remove

        Returns:
            bool: True if language was removed successfully
        """
        primary_language = language.split("-")[0]

        if primary_language in self._supported_languages and primary_language != "en":
            self._supported_languages.remove(primary_language)
            logger.info(f"Removed supported language: {primary_language}")
            return True

        return False


# Global service instance
language_detection_service = LanguageDetectionService()
