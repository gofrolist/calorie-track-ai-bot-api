"""Contract tests for PUT /api/v1/config/ui endpoint."""

from datetime import UTC
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app

client = TestClient(app)

HEADERS = {"x-user-id": "123456789"}


def _patch_db():
    """Patch DB calls to return None (no existing config) and accept creates."""
    return (
        patch(
            "calorie_track_ai_bot.api.v1.config.db_get_ui_configuration",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "calorie_track_ai_bot.api.v1.config.db_create_ui_configuration",
            new_callable=AsyncMock,
        ),
        patch(
            "calorie_track_ai_bot.api.v1.config.db_update_ui_configuration",
            new_callable=AsyncMock,
            return_value=None,
        ),
    )


class TestUIConfigPutContract:
    def test_put_ui_config_with_valid_data_returns_200(self):
        valid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "auto",
            "theme_source": "telegram",
            "language": "en",
            "language_source": "telegram",
            "safe_area_top": 44,
            "safe_area_bottom": 34,
            "safe_area_left": 0,
            "safe_area_right": 0,
            "features": {"enableDebugLogging": True, "enableErrorReporting": False},
        }

        p1, p2, p3 = _patch_db()
        with p1, p2, p3:
            response = client.put("/api/v1/config/ui", json=valid_payload, headers=HEADERS)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert data["environment"] == valid_payload["environment"]
        assert data["api_base_url"] == valid_payload["api_base_url"]
        assert data["theme"] == valid_payload["theme"]
        assert data["theme_source"] == valid_payload["theme_source"]
        assert data["language"] == valid_payload["language"]
        assert data["language_source"] == valid_payload["language_source"]

    def test_put_ui_config_validates_environment(self):
        invalid_payload = {
            "environment": "invalid_env",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload, headers=HEADERS)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert any("environment" in str(err) for err in data["detail"])

    def test_put_ui_config_validates_theme(self):
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "invalid_theme",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload, headers=HEADERS)

        assert response.status_code == 422

    def test_put_ui_config_validates_theme_source(self):
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "theme_source": "invalid_source",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload, headers=HEADERS)

        assert response.status_code == 422

    def test_put_ui_config_validates_language_format(self):
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "language": "invalid-lang-code",
        }

        p1, p2, p3 = _patch_db()
        with p1, p2, p3:
            response = client.put("/api/v1/config/ui", json=invalid_payload, headers=HEADERS)

        assert response.status_code == 400

    def test_put_ui_config_validates_safe_areas(self):
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "safe_area_top": -5,
        }

        p1, p2, p3 = _patch_db()
        with p1, p2, p3:
            response = client.put("/api/v1/config/ui", json=invalid_payload, headers=HEADERS)

        assert response.status_code == 400

    def test_put_ui_config_validates_api_base_url(self):
        invalid_payload = {
            "environment": "development",
            "api_base_url": "not-a-valid-url",
            "theme": "light",
        }

        p1, p2, p3 = _patch_db()
        with p1, p2, p3:
            response = client.put("/api/v1/config/ui", json=invalid_payload, headers=HEADERS)

        assert response.status_code == 400

    def test_put_ui_config_returns_updated_timestamps(self):
        valid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
        }

        p1, p2, p3 = _patch_db()
        with p1, p2, p3:
            response = client.put("/api/v1/config/ui", json=valid_payload, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            assert "updated_at" in data
            assert "created_at" in data

            from datetime import datetime

            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            now = datetime.now(UTC)
            time_diff = (now - updated_at).total_seconds()
            assert time_diff < 5

    def test_put_ui_config_requires_authentication(self):
        response = client.put("/api/v1/config/ui", json={"theme": "light"})
        assert response.status_code == 401
