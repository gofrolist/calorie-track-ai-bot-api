"""
Contract tests for GET /health/connectivity endpoint.

This test validates the API contract for connectivity health checks
between frontend and backend systems.
"""

from uuid import UUID

from fastapi.testclient import TestClient

from calorie_track_ai_bot.main import app

client = TestClient(app)


class TestHealthConnectivityContract:
    """Test contract compliance for health connectivity endpoint."""

    def test_get_health_connectivity_returns_200_with_valid_schema(self):
        """Test that GET /health/connectivity returns 200 with valid response schema."""
        response = client.get("/health/connectivity")

        # Should return 200 status
        assert response.status_code == 200

        # Should return JSON
        assert response.headers["content-type"] == "application/json"

        # Validate response schema
        data = response.json()
        assert "status" in data
        assert "response_time_ms" in data
        assert "timestamp" in data
        assert "correlation_id" in data

        # Validate field types and constraints
        assert data["status"] in ["connected", "disconnected", "error"]
        assert isinstance(data["response_time_ms"], int | float)
        assert data["response_time_ms"] >= 0
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["correlation_id"], str)

        # Validate correlation_id is a valid UUID
        UUID(data["correlation_id"])  # Should not raise exception

        # Validate timestamp format (ISO 8601)
        from datetime import datetime

        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_get_health_connectivity_performance_requirement(self):
        """Test that connectivity check completes within performance requirements."""
        import time

        start_time = time.time()
        response = client.get("/health/connectivity")
        end_time = time.time()

        # Should complete within 200ms (as per FR-005)
        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 200, (
            f"Response time {response_time_ms}ms exceeds 200ms requirement"
        )

        # Response should also include timing
        data = response.json()
        assert data["response_time_ms"] < 200

    def test_get_health_connectivity_cors_headers(self):
        """Test that CORS headers are properly set for cross-origin requests."""
        # Make preflight request
        response = client.options(
            "/health/connectivity",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should allow CORS
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_get_health_connectivity_error_handling(self):
        """Test error handling returns proper error response format."""
        # This test will fail initially as endpoint doesn't exist
        # When endpoint returns 500, it should follow error response schema
        pass  # Implementation will be added after endpoint exists

    def test_get_health_connectivity_idempotency(self):
        """Test that multiple calls to connectivity check are idempotent."""
        # Make multiple requests
        responses = [client.get("/health/connectivity") for _ in range(3)]

        # All should return 200
        for response in responses:
            assert response.status_code == 200

        # All should have different correlation IDs but same status structure
        correlation_ids = [response.json()["correlation_id"] for response in responses]
        assert len(set(correlation_ids)) == 3  # All unique
