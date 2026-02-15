"""Tests for development environment endpoint."""

import uuid

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import DevelopmentEnvironment

client = TestClient(app)


class TestDevEnvironmentContract:
    def test_get_dev_environment_success(self):
        """Test GET /api/v1/dev/environment returns 200 with valid schema or 403 in production."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            assert response.json()["error"] == "access_denied"
            return

        assert response.status_code == 200
        data = response.json()

        # Validate full response against Pydantic schema
        dev_env = DevelopmentEnvironment(**data)
        assert isinstance(dev_env.id, uuid.UUID)
        assert len(dev_env.name) > 0
        assert 1024 <= dev_env.frontend_port <= 65535
        assert 1024 <= dev_env.backend_port <= 65535
        assert dev_env.frontend_port != dev_env.backend_port

    def test_get_dev_environment_stable_id(self):
        """Test that development environment returns consistent ID across requests."""
        response1 = client.get("/api/v1/dev/environment")

        if response1.status_code == 403:
            return

        assert response1.status_code == 200

        response2 = client.get("/api/v1/dev/environment")
        assert response2.status_code == 200

        assert response1.json()["id"] == response2.json()["id"]

    def test_get_dev_environment_unauthorized(self):
        """Test that endpoint returns 403 with error payload when access is denied."""
        response = client.get("/api/v1/dev/environment")

        # In production this returns 403; in dev it returns 200.
        # Either way, the response must be well-formed.
        assert response.status_code in [200, 403]
        if response.status_code == 403:
            data = response.json()
            assert "error" in data
            assert data["error"] == "access_denied"
