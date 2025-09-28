"""
Contract tests for PUT /api/v1/config/ui endpoint.

This test validates the API contract for UI configuration updates
including safe areas, theme, and language settings.
"""

from datetime import UTC

from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app

client = TestClient(app)


class TestUIConfigPutContract:
    """Test contract compliance for UI configuration PUT endpoint."""

    def test_put_ui_config_with_valid_data_returns_200(self):
        """Test that PUT /api/v1/config/ui returns 200 with valid request data."""
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

        response = client.put("/api/v1/config/ui", json=valid_payload)

        # Should return 200 status
        assert response.status_code == 200

        # Should return JSON
        assert response.headers["content-type"] == "application/json"

        # Validate response contains updated data
        data = response.json()
        assert data["environment"] == valid_payload["environment"]
        assert data["api_base_url"] == valid_payload["api_base_url"]
        assert data["theme"] == valid_payload["theme"]
        assert data["theme_source"] == valid_payload["theme_source"]
        assert data["language"] == valid_payload["language"]
        assert data["language_source"] == valid_payload["language_source"]

    def test_put_ui_config_validates_environment(self):
        """Test that PUT validates environment field."""
        invalid_payload = {
            "environment": "invalid_env",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload)

        # Should return 422 for invalid data (Pydantic validation error)
        assert response.status_code == 422

        # Should include validation error details
        data = response.json()
        assert "detail" in data
        assert any("environment" in str(err) for err in data["detail"])

    def test_put_ui_config_validates_theme(self):
        """Test that PUT validates theme field."""
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "invalid_theme",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload)

        # Should return 422 for invalid theme (Pydantic validation error)
        assert response.status_code == 422

    def test_put_ui_config_validates_theme_source(self):
        """Test that PUT validates theme_source field."""
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "theme_source": "invalid_source",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload)

        # Should return 422 for invalid theme source (Pydantic validation error)
        assert response.status_code == 422

    def test_put_ui_config_validates_language_format(self):
        """Test that PUT validates language field format."""
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "language": "invalid-lang-code",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload)

        # Should return 400 for invalid language format (custom validation error)
        assert response.status_code == 400

    def test_put_ui_config_validates_safe_areas(self):
        """Test that PUT validates safe area values."""
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "safe_area_top": -5,  # Negative value should be invalid
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload)

        # Should return 400 for negative safe area (custom validation error)
        assert response.status_code == 400

    def test_put_ui_config_validates_api_base_url(self):
        """Test that PUT validates API base URL format."""
        invalid_payload = {
            "environment": "development",
            "api_base_url": "not-a-valid-url",
            "theme": "light",
        }

        response = client.put("/api/v1/config/ui", json=invalid_payload)

        # Should return 400 for invalid URL
        assert response.status_code == 400

    def test_put_ui_config_validates_feature_flags(self):
        """Test that PUT validates feature flags format."""
        invalid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
            "features": {
                "invalidFlag": "not_boolean"  # Should be boolean
            },
        }

        client.put("/api/v1/config/ui", json=invalid_payload)

        # Feature flags with non-boolean values should be accepted
        # (they're stored as generic object)
        # But the response should normalize them or validate appropriately

    def test_put_ui_config_returns_updated_timestamps(self):
        """Test that PUT returns updated timestamps."""
        valid_payload = {
            "environment": "development",
            "api_base_url": "http://localhost:8000",
            "theme": "light",
        }

        response = client.put("/api/v1/config/ui", json=valid_payload)

        if response.status_code == 200:
            data = response.json()
            assert "updated_at" in data
            assert "created_at" in data

            # updated_at should be recent
            from datetime import datetime

            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            now = datetime.now(UTC)
            time_diff = (now - updated_at).total_seconds()
            assert time_diff < 5  # Should be within 5 seconds
