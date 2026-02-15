"""Contract tests for GET /api/v1/config/ui endpoint."""

from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app

client = TestClient(app)

HEADERS = {"x-user-id": "123456789"}


class TestUIConfigGetContract:
    def test_get_ui_config_returns_200_with_valid_schema(self):
        with (
            patch(
                "calorie_track_ai_bot.api.v1.config.db_get_ui_configuration",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.config.db_create_ui_configuration",
                new_callable=AsyncMock,
            ),
        ):
            response = client.get("/api/v1/config/ui", headers=HEADERS)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        required_fields = ["id", "environment", "api_base_url", "theme", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing"

        UUID(data["id"])
        assert data["environment"] in ["development", "production"]
        assert data["api_base_url"].startswith(("http://", "https://"))
        assert data["theme"] in ["light", "dark", "auto"]

    def test_get_ui_config_requires_authentication(self):
        response = client.get("/api/v1/config/ui")
        assert response.status_code == 401

    def test_get_ui_config_safe_areas_validation(self):
        with (
            patch(
                "calorie_track_ai_bot.api.v1.config.db_get_ui_configuration",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.config.db_create_ui_configuration",
                new_callable=AsyncMock,
            ),
        ):
            response = client.get("/api/v1/config/ui", headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            safe_area_fields = [
                "safe_area_top",
                "safe_area_bottom",
                "safe_area_left",
                "safe_area_right",
            ]
            for field in safe_area_fields:
                if field in data:
                    value = data[field]
                    assert 0 <= value <= 100, f"Safe area {field} should be between 0-100px"

    def test_get_ui_config_feature_flags(self):
        with (
            patch(
                "calorie_track_ai_bot.api.v1.config.db_get_ui_configuration",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.config.db_create_ui_configuration",
                new_callable=AsyncMock,
            ),
        ):
            response = client.get("/api/v1/config/ui", headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                assert isinstance(data["features"], dict)
                for key, value in data["features"].items():
                    assert isinstance(value, bool), f"Feature flag '{key}' should be boolean"

    def test_get_ui_config_timestamp_format(self):
        with (
            patch(
                "calorie_track_ai_bot.api.v1.config.db_get_ui_configuration",
                new_callable=AsyncMock,
                return_value=None,
            ),
            patch(
                "calorie_track_ai_bot.api.v1.config.db_create_ui_configuration",
                new_callable=AsyncMock,
            ),
        ):
            response = client.get("/api/v1/config/ui", headers=HEADERS)

        if response.status_code == 200:
            data = response.json()
            from datetime import datetime

            for field in ["created_at", "updated_at"]:
                if field in data:
                    datetime.fromisoformat(data[field].replace("Z", "+00:00"))
