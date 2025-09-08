"""Tests for health API endpoints."""

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.api.v1.health import router


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_live_endpoint(self, client):
        """Test /live endpoint."""
        response = client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}

    def test_ready_endpoint(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}

    def test_health_endpoints_content_type(self, client):
        """Test that health endpoints return JSON."""
        live_response = client.get("/live")
        ready_response = client.get("/ready")

        assert live_response.headers["content-type"] == "application/json"
        assert ready_response.headers["content-type"] == "application/json"

    def test_health_endpoints_methods(self, client):
        """Test that health endpoints only accept GET requests."""
        # Test live endpoint
        live_post = client.post("/live")
        assert live_post.status_code == 405  # Method Not Allowed

        live_put = client.put("/live")
        assert live_put.status_code == 405

        # Test ready endpoint
        ready_post = client.post("/ready")
        assert ready_post.status_code == 405

        ready_put = client.put("/ready")
        assert ready_put.status_code == 405

    def test_health_endpoints_response_structure(self, client):
        """Test that health endpoints return consistent response structure."""
        live_response = client.get("/live")
        ready_response = client.get("/ready")

        live_data = live_response.json()
        ready_data = ready_response.json()

        # Both should have the same structure
        assert "status" in live_data
        assert "status" in ready_data
        assert live_data["status"] == ready_data["status"]
        assert live_data["status"] == "ok"
