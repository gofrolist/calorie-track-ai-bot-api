import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import Theme, ThemeDetectionResponse, ThemeSource

client = TestClient(app)


class TestConfigThemeContract:
    def test_get_theme_config_returns_200_with_valid_schema(self):
        """Test that GET /api/v1/config/theme returns 200 with valid response schema."""
        response = client.get("/api/v1/config/theme")

        assert response.status_code == 200
        data = response.json()

        # Validate response against schema
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
        """Test theme detection with Telegram WebApp headers."""
        response = client.get(
            "/api/v1/config/theme",
            headers={
                "x-telegram-color-scheme": "dark",
                "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] in ["light", "dark", "auto"]
        assert data["theme_source"] in ["telegram", "system", "manual"]

    def test_get_theme_config_with_system_preference(self):
        """Test theme detection with system preference headers."""
        response = client.get(
            "/api/v1/config/theme", headers={"sec-ch-prefers-color-scheme": "dark"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["theme"] in ["light", "dark", "auto"]
        assert data["theme_source"] in ["telegram", "system", "manual"]

    def test_get_theme_config_validates_correlation_id(self):
        """Test that correlation ID is properly handled."""
        correlation_id = str(uuid.uuid4())
        response = client.get("/api/v1/config/theme", headers={"x-correlation-id": correlation_id})

        assert response.status_code == 200
        # Correlation ID should be logged, but not necessarily returned in response

    def test_get_theme_config_handles_authentication(self):
        """Test theme detection with user authentication."""
        response = client.get("/api/v1/config/theme", headers={"x-user-id": "test-user-123"})

        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "theme_source" in data

    def test_get_theme_config_performance_requirement(self):
        """Test that theme detection response time is under 200ms."""
        import time

        start_time = time.perf_counter()
        response = client.get("/api/v1/config/theme")
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )
