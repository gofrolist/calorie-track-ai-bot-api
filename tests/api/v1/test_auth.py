"""Tests for auth API endpoints."""

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.auth import router


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_telegram_init_endpoint(self, client):
        """Test /auth/telegram/init endpoint."""
        response = client.post("/auth/telegram/init")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data

        # Check values (currently hardcoded to "dev")
        assert data["token"] == "dev"
        assert data["refresh_token"] == "dev"
        assert data["user"]["id"] == "dev"

    def test_telegram_init_response_structure(self, client):
        """Test that telegram init returns proper JSON structure."""
        response = client.post("/auth/telegram/init")
        data = response.json()

        # Should be valid JSON
        assert isinstance(data, dict)

        # Should have required fields
        required_fields = ["token", "refresh_token", "user"]
        for field in required_fields:
            assert field in data

        # User should be a dict with id
        assert isinstance(data["user"], dict)
        assert "id" in data["user"]

    def test_telegram_init_methods(self, client):
        """Test that telegram init only accepts POST requests."""
        get_response = client.get("/auth/telegram/init")
        assert get_response.status_code == 405  # Method Not Allowed

        put_response = client.put("/auth/telegram/init")
        assert put_response.status_code == 405

        delete_response = client.delete("/auth/telegram/init")
        assert delete_response.status_code == 405

    def test_telegram_init_content_type(self, client):
        """Test that telegram init returns JSON content type."""
        response = client.post("/auth/telegram/init")
        assert response.headers["content-type"] == "application/json"

    def test_telegram_init_multiple_calls(self, client):
        """Test that multiple calls to telegram init return consistent data."""
        response1 = client.post("/auth/telegram/init")
        response2 = client.post("/auth/telegram/init")

        data1 = response1.json()
        data2 = response2.json()

        # Should return the same data (currently hardcoded)
        assert data1 == data2
        assert data1["token"] == data2["token"]
        assert data1["refresh_token"] == data2["refresh_token"]
        assert data1["user"]["id"] == data2["user"]["id"]
