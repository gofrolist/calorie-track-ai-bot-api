import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import ServiceStatus, SupabaseStatus

client = TestClient(app)


class TestDevSupabaseStatusContract:
    def test_get_supabase_status_returns_200_with_valid_schema(self):
        """Test that GET /api/v1/dev/supabase/status returns 200 with valid response schema."""
        response = client.get("/api/v1/dev/supabase/status")

        # Should return 200 in development environment
        if response.status_code == 403:
            # Access denied in production - this is expected behavior
            assert response.json()["error"] == "access_denied"
            return

        assert response.status_code == 200
        data = response.json()

        # Validate response against schema
        supabase_status = SupabaseStatus(**data)
        assert isinstance(supabase_status.status, ServiceStatus)
        assert supabase_status.status in [
            ServiceStatus.running,
            ServiceStatus.stopped,
            ServiceStatus.error,
        ]
        assert isinstance(supabase_status.db_port, int)
        assert supabase_status.db_port == 54322  # Standard Supabase local port
        assert isinstance(supabase_status.services, dict)
        assert "db" in supabase_status.services
        assert isinstance(supabase_status.services["db"], bool)
        assert isinstance(supabase_status.last_check, datetime)

    def test_get_supabase_status_validates_database_port(self):
        """Test that Supabase status returns correct database port."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        # Should always be port 54322 for Supabase database
        assert data["db_port"] == 54322

    def test_get_supabase_status_includes_database_url(self):
        """Test that Supabase status includes database URL."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        assert "database_url" in data
        assert isinstance(data["database_url"], str)

        # Should be a valid database URL
        if data["database_url"]:
            assert "postgresql://" in data["database_url"]
            assert "localhost" in data["database_url"]
            assert "54322" in data["database_url"]

    def test_get_supabase_status_validates_service_status(self):
        """Test that Supabase status has valid service status."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        assert data["status"] in ["running", "stopped", "error"]

        # Service status should be consistent with overall status
        if data["status"] == "running":
            assert data["services"]["db"] is True
        elif data["status"] in ["stopped", "error"]:
            assert data["services"]["db"] is False

    def test_get_supabase_status_includes_version_info(self):
        """Test that Supabase status includes version information when available."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        # Version may be null if Supabase is not running
        assert "version" in data
        if data["version"] is not None:
            assert isinstance(data["version"], str)
            assert len(data["version"]) > 0

    def test_get_supabase_status_handles_cli_not_available(self):
        """Test that endpoint handles case when Supabase CLI is not available."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        # Should return 200 even when CLI is not available
        assert response.status_code == 200
        data = response.json()

        # When CLI is not available, status should be "error"
        if data["status"] == "error":
            assert data["services"]["db"] is False
            assert data["version"] is None

    def test_get_supabase_status_includes_uptime_when_running(self):
        """Test that Supabase status includes uptime when service is running."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        # Uptime should be present when service is running
        assert "uptime_seconds" in data
        if data["status"] == "running" and data["uptime_seconds"] is not None:
            assert isinstance(data["uptime_seconds"], int | float)
            assert data["uptime_seconds"] >= 0

    def test_get_supabase_status_with_correlation_id(self):
        """Test Supabase status endpoint with correlation ID."""
        correlation_id = str(uuid.uuid4())
        response = client.get(
            "/api/v1/dev/supabase/status", headers={"x-correlation-id": correlation_id}
        )

        assert response.status_code in [200, 403]

    def test_get_supabase_status_with_authentication(self):
        """Test Supabase status endpoint with user authentication."""
        response = client.get("/api/v1/dev/supabase/status", headers={"x-user-id": "dev-user-456"})

        assert response.status_code in [200, 403]

    def test_get_supabase_status_caching_behavior(self):
        """Test that Supabase status implements caching for performance."""
        import time

        # First request
        start_time1 = time.perf_counter()
        response1 = client.get("/api/v1/dev/supabase/status")
        end_time1 = time.perf_counter()

        if response1.status_code == 403:
            return

        # Second request (should be faster due to caching)
        start_time2 = time.perf_counter()
        response2 = client.get("/api/v1/dev/supabase/status")
        end_time2 = time.perf_counter()

        assert response1.status_code == 200
        assert response2.status_code == 200

        response_time1_ms = (end_time1 - start_time1) * 1000
        response_time2_ms = (end_time2 - start_time2) * 1000

        # Second request should be faster or similar (cached)
        # Allow some variance for test execution
        assert response_time2_ms <= response_time1_ms + 50

    def test_get_supabase_status_performance_requirement(self):
        """Test that Supabase status response time is under 200ms."""
        import time

        start_time = time.perf_counter()
        response = client.get("/api/v1/dev/supabase/status")
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code in [200, 403]
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )

    def test_get_supabase_status_timeout_handling(self):
        """Test that endpoint handles timeouts gracefully."""
        response = client.get("/api/v1/dev/supabase/status")

        if response.status_code == 403:
            return

        # Should not return 504 (timeout) under normal circumstances
        # If CLI takes too long, should return status="error" instead
        assert response.status_code != 504
        assert response.status_code == 200

        data = response.json()
        if data["status"] == "error":
            # Error status is acceptable for timeout scenarios
            assert data["services"]["db"] is False
