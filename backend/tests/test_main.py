"""Tests for main application."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app


class TestMainApplication:
    """Test main FastAPI application."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_app_title(self, client):
        """Test that app has correct title."""
        # Get OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert schema["info"]["title"] == "Calories Count API"
        assert schema["info"]["version"] == "0.1.0"

    def test_health_endpoints_available(self, client):
        """Test that health endpoints are available."""
        # Test live endpoint
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Test ready endpoint
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Test healthz endpoint (for Fly.io)
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_auth_endpoints_available(self, client):
        """Test that auth endpoints are available."""
        response = client.post("/api/v1/auth/telegram/init")
        assert response.status_code == 200

        data = response.json()
        assert "token" in data
        assert "refresh_token" in data
        assert "user" in data

    def test_photos_endpoints_available(self, client):
        """Test that photos endpoints are available."""
        # Test that endpoint exists (will fail validation but endpoint exists)
        response = client.post("/api/v1/photos")
        assert response.status_code == 422  # Validation error, but endpoint exists

    def test_estimates_endpoints_available(self, client):
        """Test that estimates endpoints are available."""
        with (
            patch("calorie_track_ai_bot.services.queue.enqueue_estimate_job") as mock_enqueue,
            patch("calorie_track_ai_bot.services.db.get_pool"),
            patch("calorie_track_ai_bot.api.v1.estimates.db_get_estimate") as mock_get_est,
        ):
            mock_enqueue.return_value = "job-123"
            mock_get_est.return_value = None

            # Test estimate photo endpoint
            response = client.post("/api/v1/photos/test123/estimate")
            assert response.status_code in [200, 500]

            # Test get estimate endpoint
            response = client.get("/api/v1/estimates/test123")
            assert response.status_code in [404, 500]

    def test_meals_endpoints_available(self, client):
        """Test that meals endpoints are available."""
        # Test that endpoint exists (will fail validation but endpoint exists)
        response = client.post("/api/v1/meals")
        assert response.status_code == 422  # Validation error, but endpoint exists

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        # Make a regular request with Origin header to test CORS
        response = client.get("/health/live", headers={"Origin": "http://localhost:5173"})

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"

    def test_cors_preflight_request(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/api/v1/photos",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should return 200 for preflight
        assert response.status_code == 200

        # Should have CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers

    def test_openapi_docs_available(self, client):
        """Test that OpenAPI docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200

        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_available(self, client):
        """Test that OpenAPI JSON is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema

    def test_router_prefixes(self, client):
        """Test that routers are mounted with correct prefixes."""
        # Health endpoints should be under /health
        response = client.get("/health/live")
        assert response.status_code == 200

        # API endpoints should be under /api/v1
        response = client.post("/api/v1/auth/telegram/init")
        assert response.status_code == 200

    def test_404_for_nonexistent_endpoints(self, client):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

        response = client.post("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_app_startup(self, client):
        """Test that app starts up correctly."""
        # Just making sure the app can be instantiated and basic endpoints work
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_all_routers_included(self, client):
        """Test that all expected routers are included."""
        # Get OpenAPI schema to check paths
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # Check that all expected paths exist
        expected_paths = [
            "/health/live",
            "/health/ready",
            "/healthz",
            "/api/v1/auth/telegram/init",
            "/api/v1/photos",
            "/api/v1/photos/{photo_id}/estimate",
            "/api/v1/estimates/{estimate_id}",
            "/api/v1/meals",
        ]

        for path in expected_paths:
            assert path in paths, f"Path {path} not found in OpenAPI schema"
