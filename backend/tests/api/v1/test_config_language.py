import re
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import LanguageDetectionResponse, LanguageSource

client = TestClient(app)


class TestConfigLanguageContract:
    def test_get_language_config_returns_200_with_valid_schema(self):
        """Test that GET /api/v1/config/language returns 200 with valid response schema."""
        response = client.get("/api/v1/config/language")

        assert response.status_code == 200
        data = response.json()

        # Validate response against schema
        language_response = LanguageDetectionResponse(**data)
        assert language_response.language_source in [
            LanguageSource.telegram,
            LanguageSource.browser,
            LanguageSource.manual,
        ]
        assert isinstance(language_response.detected_at, datetime)

        # Validate language code format (currently supporting only en and ru)
        # Should be one of the supported languages
        assert language_response.language in ["en", "ru"]

    def test_get_language_config_with_telegram_headers(self):
        """Test language detection with Telegram WebApp headers."""
        response = client.get(
            "/api/v1/config/language",
            headers={
                "x-telegram-language-code": "es",
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language_source"] in ["telegram", "browser", "manual"]
        assert re.match(r"^[a-z]{2}(-[A-Z]{2})?$", data["language"])

    def test_get_language_config_with_browser_preference(self):
        """Test language detection with browser Accept-Language header."""
        response = client.get(
            "/api/v1/config/language", headers={"accept-language": "fr-FR,fr;q=0.9,en;q=0.8"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language_source"] in ["telegram", "browser", "manual"]
        assert data["language"] == "en"  # Should fallback to default since French is not supported

    def test_get_language_config_validates_supported_languages(self):
        """Test that response includes supported languages list."""
        response = client.get("/api/v1/config/language")

        assert response.status_code == 200
        data = response.json()
        assert "supported_languages" in data
        assert isinstance(data["supported_languages"], list)
        assert len(data["supported_languages"]) > 0

        # Verify supported languages are the ones we currently support
        expected_languages = ["en", "ru"]
        assert data["supported_languages"] == expected_languages

    def test_get_language_config_fallback_to_default(self):
        """Test language detection fallback to default language."""
        response = client.get(
            "/api/v1/config/language",
            headers={
                "accept-language": "xx-XX"  # Invalid language
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"  # Should fallback to default
        assert data["language_source"] in ["browser", "manual"]

    def test_get_language_config_validates_correlation_id(self):
        """Test that correlation ID is properly handled."""
        correlation_id = str(uuid.uuid4())
        response = client.get(
            "/api/v1/config/language", headers={"x-correlation-id": correlation_id}
        )

        assert response.status_code == 200

    def test_get_language_config_handles_authentication(self):
        """Test language detection with user authentication."""
        response = client.get("/api/v1/config/language", headers={"x-user-id": "test-user-456"})

        assert response.status_code == 200
        data = response.json()
        assert "language" in data
        assert "language_source" in data

    def test_get_language_config_performance_requirement(self):
        """Test that language detection response time is under 200ms."""
        import time

        start_time = time.perf_counter()
        response = client.get("/api/v1/config/language")
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )
