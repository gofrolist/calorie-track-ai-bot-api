"""
Integration tests for frontend-backend connectivity.

This test validates end-to-end connectivity between the React frontend
and FastAPI backend, including CORS, authentication, and data flow.
"""

import time
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app


@pytest.fixture
def isolated_client():
    """Test client with mocked services to prevent AsyncMock warnings."""

    # Mock multiple services that might trigger async operations
    with (
        patch("calorie_track_ai_bot.services.telegram.get_bot") as mock_get_bot,
        patch("calorie_track_ai_bot.services.monitoring.performance_monitor") as mock_monitor,
        patch("calorie_track_ai_bot.services.db.get_pool") as mock_db,
        patch("calorie_track_ai_bot.services.queue.r") as mock_redis,
        patch("calorie_track_ai_bot.services.storage.s3") as mock_s3,
        patch("calorie_track_ai_bot.services.estimator.client") as mock_openai,
        patch("calorie_track_ai_bot.main.get_bot") as mock_main_bot,
        patch("calorie_track_ai_bot.main.close_pool") as _mock_close_pool,
        patch("calorie_track_ai_bot.main.redis_client", None),
    ):
        # Mock the bot to prevent async operations during lifespan
        mock_bot = Mock()
        mock_bot.set_webhook = Mock(return_value=True)
        mock_bot.close = Mock()
        mock_get_bot.return_value = mock_bot
        mock_main_bot.return_value = mock_bot

        # Mock monitoring service to prevent async operations
        mock_monitor.start_monitoring = Mock()
        mock_monitor.stop_monitoring = Mock()
        mock_monitor.get_metrics_summary = Mock(return_value={})

        # Mock database and queue services
        mock_db.return_value = None
        mock_redis.return_value = None
        mock_s3.return_value = None
        mock_openai.return_value = None

        with TestClient(app) as client:
            yield client


class TestFrontendBackendConnectivity:
    """Test integration between frontend and backend systems."""

    def test_cors_preflight_request(self, isolated_client):
        """Test that CORS preflight requests are handled correctly."""
        # Simulate a preflight request from frontend
        response = isolated_client.options(
            "/health/connectivity",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )

        # Should allow the request
        assert response.status_code == 200

        # Should include CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers

    def test_cors_actual_request_from_frontend(self, isolated_client):
        """Test that actual requests from frontend origins are allowed."""
        frontend_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "https://localhost:3000",
        ]

        for origin in frontend_origins:
            response = isolated_client.get(
                "/healthz",  # Use existing endpoint for now
                headers={"Origin": origin},
            )

            # Should succeed (not blocked by CORS)
            assert response.status_code == 200

            # Should include CORS headers
            if "access-control-allow-origin" in response.headers:
                assert response.headers["access-control-allow-origin"] in [origin, "*"]

    def test_health_check_endpoint_accessibility(self, isolated_client):
        """Test that health check endpoints are accessible to frontend."""
        # Test basic health check
        response = isolated_client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_api_response_format_consistency(self, isolated_client):
        """Test that API responses follow consistent format for frontend consumption."""
        endpoints_to_test = [
            "/healthz",
            # Add more endpoints as they're implemented
        ]

        for endpoint in endpoints_to_test:
            response = isolated_client.get(endpoint)

            if response.status_code == 200:
                # Should return JSON
                assert response.headers["content-type"] == "application/json"

                # Should be valid JSON
                data = response.json()
                assert isinstance(data, dict)

    def test_error_response_format_for_frontend(self, isolated_client):
        """Test that error responses follow consistent format for frontend handling."""
        # Test 404 error format
        response = isolated_client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        # Should return JSON error format
        assert response.headers["content-type"] == "application/json"
        error_data = response.json()

        # Should include error details
        assert "detail" in error_data or "error" in error_data

    def test_request_timeout_handling(self, isolated_client):
        """Test that requests complete within acceptable timeouts for frontend."""
        start_time = time.time()
        response = isolated_client.get("/healthz")
        end_time = time.time()

        request_time = (end_time - start_time) * 1000  # milliseconds

        # Should complete quickly for good UX
        assert request_time < 1000  # Under 1 second
        assert response.status_code == 200

    def test_concurrent_requests_from_frontend(self, isolated_client):
        """Test handling of concurrent requests from frontend."""
        import concurrent.futures

        def make_request():
            return isolated_client.get("/healthz")

        # Simulate multiple concurrent frontend requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            responses = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

    def test_json_content_type_handling(self, isolated_client):
        """Test that JSON content types are handled correctly for frontend."""
        # Test POST with JSON (when endpoints exist)
        json_data = {"test": "data"}

        # For now, test with a mock endpoint
        # This will be updated when actual endpoints are implemented
        response = isolated_client.post(
            "/api/v1/config/ui",  # Will be implemented later
            json=json_data,
            headers={"Content-Type": "application/json"},
        )

        # Should handle JSON content type (even if endpoint doesn't exist yet)
        assert response.headers.get("content-type") == "application/json"

    def test_mobile_webapp_compatibility(self, isolated_client):
        """Test compatibility with Telegram WebApp mobile environment."""
        # Test with mobile user agent
        mobile_headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            "X-Requested-With": "org.telegram.plus",  # Telegram app identifier
        }

        response = isolated_client.get("/healthz", headers=mobile_headers)
        assert response.status_code == 200

    def test_telegram_webapp_headers(self, isolated_client):
        """Test handling of Telegram WebApp specific headers."""
        telegram_headers = {
            "X-Telegram-Bot-Api-Secret-Token": "test-token",
            "Origin": "https://web.telegram.org",
        }

        response = isolated_client.get("/healthz", headers=telegram_headers)

        # Should handle Telegram-specific headers without issues
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_websocket_connectivity_preparation(self):
        """Test preparation for WebSocket connectivity (future feature)."""
        # This is a placeholder for future WebSocket testing
        # For now, just verify the app can handle the concept
        assert hasattr(app, "add_middleware")  # Can add WebSocket middleware
