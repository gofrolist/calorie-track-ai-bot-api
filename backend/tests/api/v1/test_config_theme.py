import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import Theme, ThemeDetectionResponse, ThemeSource

client = TestClient(app)

HEADERS = {"x-user-id": "123456789"}


class TestConfigThemeContract:
    def test_get_theme_config_returns_200_with_valid_schema(self):
        response = client.get("/api/v1/config/theme", headers=HEADERS)

        assert response.status_code == 200
        data = response.json()

        theme_response = ThemeDetectionResponse(**data)
        assert theme_response.theme in [Theme.light, Theme.dark, Theme.auto]
        assert theme_response.theme_source in [
            ThemeSource.telegram,
            ThemeSource.system,
            ThemeSource.manual,
        ]
        assert (
            isinstance(theme_response.telegram_color_scheme, str)
            or theme_response.telegram_color_scheme is None
        )
        assert isinstance(theme_response.system_prefers_dark, bool)
        assert isinstance(theme_response.detected_at, datetime)

    def test_get_theme_config_with_telegram_headers(self):
        response = client.get(
            "/api/v1/config/theme",
            headers={
                **HEADERS,
                "x-telegram-color-scheme": "dark",
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] in ["light", "dark", "auto"]
        assert data["theme_source"] in ["telegram", "system", "manual"]

    def test_get_theme_config_with_system_preference(self):
        response = client.get(
            "/api/v1/config/theme",
            headers={**HEADERS, "sec-ch-prefers-color-scheme": "dark"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] in ["light", "dark", "auto"]
        assert data["theme_source"] in ["telegram", "system", "manual"]

    def test_get_theme_config_validates_correlation_id(self):
        correlation_id = str(uuid.uuid4())
        response = client.get(
            "/api/v1/config/theme",
            headers={**HEADERS, "x-correlation-id": correlation_id},
        )

        assert response.status_code == 200

    def test_get_theme_config_requires_authentication(self):
        response = client.get("/api/v1/config/theme")
        assert response.status_code == 401

    def test_get_theme_config_performance_requirement(self):
        import time

        start_time = time.perf_counter()
        response = client.get("/api/v1/config/theme", headers=HEADERS)
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )
