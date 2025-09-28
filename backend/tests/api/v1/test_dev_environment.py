import uuid
from datetime import datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import DevelopmentEnvironment

client = TestClient(app)


class TestDevEnvironmentContract:
    def test_get_dev_environment_returns_200_with_valid_schema(self):
        """Test that GET /api/v1/dev/environment returns 200 with valid response schema."""
        response = client.get("/api/v1/dev/environment")

        # Should return 200 in development environment
        if response.status_code == 403:
            # Access denied in production - this is expected behavior
            assert response.json()["error"] == "access_denied"
            return

        assert response.status_code == 200
        data = response.json()

        # Validate response against schema
        dev_env = DevelopmentEnvironment(**data)
        assert isinstance(dev_env.id, uuid.UUID)
        assert isinstance(dev_env.name, str)
        assert len(dev_env.name) > 0
        assert isinstance(dev_env.frontend_port, int)
        assert isinstance(dev_env.backend_port, int)
        assert 1024 <= dev_env.frontend_port <= 65535
        assert 1024 <= dev_env.backend_port <= 65535
        assert isinstance(dev_env.created_at, datetime)
        assert isinstance(dev_env.updated_at, datetime)

    def test_get_dev_environment_validates_ports(self):
        """Test that development environment has valid port configurations."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            # Access denied in production
            return

        assert response.status_code == 200
        data = response.json()

        # Validate port ranges
        assert data["frontend_port"] >= 1024
        assert data["frontend_port"] <= 65535
        assert data["backend_port"] >= 1024
        assert data["backend_port"] <= 65535

        # Ports should be different
        assert data["frontend_port"] != data["backend_port"]

    def test_get_dev_environment_includes_database_config(self):
        """Test that development environment includes database configuration."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        # Should include Supabase database configuration
        assert "supabase_db_url" in data
        assert "supabase_db_password" in data
        assert isinstance(data["supabase_db_url"], str)
        assert len(data["supabase_db_url"]) > 0

    def test_get_dev_environment_includes_cors_config(self):
        """Test that development environment includes CORS configuration."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        # Should include CORS origins
        assert "cors_origins" in data
        assert isinstance(data["cors_origins"], list)

        # In development, should allow localhost origins
        if data.get("cors_origins"):
            localhost_origins = [
                origin
                for origin in data["cors_origins"]
                if "localhost" in origin or "127.0.0.1" in origin
            ]
            assert len(localhost_origins) > 0

    def test_get_dev_environment_validates_log_level(self):
        """Test that development environment has valid log level."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        assert "log_level" in data
        assert data["log_level"] in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_get_dev_environment_includes_hot_reload_config(self):
        """Test that development environment includes hot reload configuration."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        assert "hot_reload" in data
        assert isinstance(data["hot_reload"], bool)

    def test_get_dev_environment_includes_cli_version(self):
        """Test that development environment includes CLI version information."""
        response = client.get("/api/v1/dev/environment")

        if response.status_code == 403:
            return

        assert response.status_code == 200
        data = response.json()

        assert "supabase_cli_version" in data
        assert isinstance(data["supabase_cli_version"], str)
        assert len(data["supabase_cli_version"]) > 0

    def test_get_dev_environment_with_correlation_id(self):
        """Test development environment endpoint with correlation ID."""
        correlation_id = str(uuid.uuid4())
        response = client.get(
            "/api/v1/dev/environment", headers={"x-correlation-id": correlation_id}
        )

        # Should handle correlation ID properly regardless of success/failure
        assert response.status_code in [200, 403]

    def test_get_dev_environment_with_authentication(self):
        """Test development environment endpoint with user authentication."""
        response = client.get("/api/v1/dev/environment", headers={"x-user-id": "dev-user-123"})

        assert response.status_code in [200, 403]

    def test_get_dev_environment_stable_id(self):
        """Test that development environment returns stable ID across requests."""
        response1 = client.get("/api/v1/dev/environment")

        if response1.status_code == 403:
            return

        assert response1.status_code == 200

        response2 = client.get("/api/v1/dev/environment")
        assert response2.status_code == 200

        # IDs should be the same (stable environment)
        assert response1.json()["id"] == response2.json()["id"]

    def test_get_dev_environment_performance_requirement(self):
        """Test that development environment response time is under 200ms."""
        import time

        start_time = time.perf_counter()
        response = client.get("/api/v1/dev/environment")
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code in [200, 403]
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )
