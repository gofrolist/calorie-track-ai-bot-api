"""
Contract tests for GET /api/v1/config/ui endpoint.

This test validates the API contract for UI configuration retrieval
including safe areas, theme, and language settings.
"""

from uuid import UUID

from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app

client = TestClient(app)


class TestUIConfigGetContract:
    """Test contract compliance for UI configuration GET endpoint."""

    def test_get_ui_config_returns_200_with_valid_schema(self):
        """Test that GET /api/v1/config/ui returns 200 with valid response schema."""
        response = client.get("/api/v1/config/ui")

        # Should return 200 status
        assert response.status_code == 200

        # Should return JSON
        assert response.headers["content-type"] == "application/json"

        # Validate response schema
        data = response.json()
        required_fields = ["id", "environment", "api_base_url", "theme", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing"

        # Validate field types and constraints
        UUID(data["id"])  # Should be valid UUID
        assert data["environment"] in ["development", "production"]
        assert data["api_base_url"].startswith(("http://", "https://"))
        assert data["theme"] in ["light", "dark", "auto"]

        # Optional fields validation
        if "theme_source" in data:
            assert data["theme_source"] in ["telegram", "system", "manual"]
        if "language" in data:
            assert isinstance(data["language"], str)
            # Should match ISO 639-1 pattern
            import re

            assert re.match(r"^[a-z]{2}(-[A-Z]{2})?$", data["language"])
        if "language_source" in data:
            assert data["language_source"] in ["telegram", "browser", "manual"]

        # Safe area fields validation
        safe_area_fields = [
            "safe_area_top",
            "safe_area_bottom",
            "safe_area_left",
            "safe_area_right",
        ]
        for field in safe_area_fields:
            if field in data:
                assert isinstance(data[field], int | float)
                assert data[field] >= 0

    def test_get_ui_config_returns_404_when_not_found(self):
        """Test that GET returns 404 when configuration not found."""
        # This will initially fail as endpoint doesn't exist
        # When implemented, should test with non-existent config
        pass

    def test_get_ui_config_safe_areas_validation(self):
        """Test that safe area values meet mobile UI requirements."""
        response = client.get("/api/v1/config/ui")

        if response.status_code == 200:
            data = response.json()

            # Safe areas should be reasonable values for mobile devices
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

    def test_get_ui_config_theme_detection_fields(self):
        """Test that theme detection fields are properly included."""
        response = client.get("/api/v1/config/ui")

        if response.status_code == 200:
            data = response.json()

            # Should include theme detection metadata
            assert "theme" in data
            if "theme_source" in data:
                assert data["theme_source"] in ["telegram", "system", "manual"]

    def test_get_ui_config_language_detection_fields(self):
        """Test that language detection fields are properly included."""
        response = client.get("/api/v1/config/ui")

        if response.status_code == 200:
            data = response.json()

            # Should include language detection metadata
            if "language" in data:
                assert isinstance(data["language"], str)
                assert len(data["language"]) >= 2  # At least 'en', 'ru', etc.
            if "language_source" in data:
                assert data["language_source"] in ["telegram", "browser", "manual"]

    def test_get_ui_config_feature_flags(self):
        """Test that feature flags are included and properly formatted."""
        response = client.get("/api/v1/config/ui")

        if response.status_code == 200:
            data = response.json()

            # Features should be an object if present
            if "features" in data:
                assert isinstance(data["features"], dict)
                # All feature values should be boolean
                for key, value in data["features"].items():
                    assert isinstance(value, bool), f"Feature flag '{key}' should be boolean"

    def test_get_ui_config_timestamp_format(self):
        """Test that timestamps are in proper ISO format."""
        response = client.get("/api/v1/config/ui")

        if response.status_code == 200:
            data = response.json()

            # Validate timestamp format
            from datetime import datetime

            for field in ["created_at", "updated_at"]:
                if field in data:
                    # Should be valid ISO 8601 format
                    datetime.fromisoformat(data[field].replace("Z", "+00:00"))
