import re
import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import LanguageDetectionResponse, LanguageSource

client = TestClient(app)

HEADERS = {"x-user-id": "123456789"}


class TestConfigLanguageContract:
    def test_get_language_config_returns_200_with_valid_schema(self):
        response = client.get("/api/v1/config/language", headers=HEADERS)

        assert response.status_code == 200
        data = response.json()

        language_response = LanguageDetectionResponse(**data)
        assert language_response.language_source in [
            LanguageSource.telegram,
            LanguageSource.browser,
            LanguageSource.manual,
        ]
        assert isinstance(language_response.detected_at, datetime)
        assert language_response.language in ["en", "ru"]

    def test_get_language_config_with_telegram_headers(self):
        response = client.get(
            "/api/v1/config/language",
            headers={
                **HEADERS,
                "x-telegram-language-code": "es",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language_source"] in ["telegram", "browser", "manual"]
        assert re.match(r"^[a-z]{2}(-[A-Z]{2})?$", data["language"])

    def test_get_language_config_with_browser_preference(self):
        response = client.get(
            "/api/v1/config/language",
            headers={**HEADERS, "accept-language": "fr-FR,fr;q=0.9,en;q=0.8"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language_source"] in ["telegram", "browser", "manual"]
        assert data["language"] == "en"

    def test_get_language_config_validates_supported_languages(self):
        response = client.get("/api/v1/config/language", headers=HEADERS)

        assert response.status_code == 200
        data = response.json()
        assert "supported_languages" in data
        assert isinstance(data["supported_languages"], list)
        assert len(data["supported_languages"]) > 0

        expected_languages = ["en", "ru"]
        assert data["supported_languages"] == expected_languages

    def test_get_language_config_fallback_to_default(self):
        response = client.get(
            "/api/v1/config/language",
            headers={**HEADERS, "accept-language": "xx-XX"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "en"
        assert data["language_source"] in ["browser", "manual"]

    def test_get_language_config_validates_correlation_id(self):
        correlation_id = str(uuid.uuid4())
        response = client.get(
            "/api/v1/config/language",
            headers={**HEADERS, "x-correlation-id": correlation_id},
        )

        assert response.status_code == 200

    def test_get_language_config_requires_authentication(self):
        response = client.get("/api/v1/config/language")
        assert response.status_code == 401

    def test_get_language_config_performance_requirement(self):
        import time

        start_time = time.perf_counter()
        response = client.get("/api/v1/config/language", headers=HEADERS)
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )
