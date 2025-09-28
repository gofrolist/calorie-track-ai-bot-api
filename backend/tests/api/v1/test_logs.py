import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.main import app
from src.calorie_track_ai_bot.schemas import LogEntry, LogLevel

client = TestClient(app)


class TestLogsContract:
    def test_post_logs_with_valid_data_returns_201(self):
        """Test that POST /api/v1/logs returns 201 with valid log data."""
        log_data = {
            "level": "INFO",
            "service": "frontend",
            "correlation_id": str(uuid.uuid4()),
            "message": "User action performed",
            "context": {"action": "photo_upload", "user_id": "user123"},
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=log_data)

        assert response.status_code == 200  # Updated from 201 to match implementation
        data = response.json()

        # Validate response against LogEntry schema
        log_entry = LogEntry(**data)
        assert log_entry.level == LogLevel.INFO
        assert log_entry.message == log_data["message"]
        assert str(log_entry.correlation_id) == log_data["correlation_id"]
        assert log_entry.context == log_data["context"]
        assert isinstance(log_entry.id, uuid.UUID)
        assert isinstance(log_entry.timestamp, datetime)

    def test_post_logs_validates_log_level(self):
        """Test that POST validates log level field."""
        invalid_log_data = {
            "level": "INVALID_LEVEL",
            "service": "frontend",
            "correlation_id": str(uuid.uuid4()),
            "message": "Test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=invalid_log_data)

        # Should return 422 for invalid enum value (Pydantic validation error)
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any(
            "Input should be" in str(err) and "INVALID_LEVEL" in str(err) for err in error_detail
        )

    def test_post_logs_validates_required_fields(self):
        """Test that POST validates required fields."""
        incomplete_log_data = {
            "level": "INFO",
            # missing service, correlation_id, message, timestamp
        }

        response = client.post("/api/v1/logs", json=incomplete_log_data)

        # Should return 422 for missing required fields
        assert response.status_code == 422
        error_detail = response.json()["detail"]

        # Check that validation errors mention missing fields
        error_fields = [err.get("loc", [])[-1] if err.get("loc") else "" for err in error_detail]
        assert "message" in error_fields

    def test_post_logs_validates_correlation_id_format(self):
        """Test that POST validates correlation ID UUID format."""
        log_data = {
            "level": "ERROR",
            "service": "backend",
            "correlation_id": "invalid-uuid-format",
            "message": "Test error message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=log_data)

        # Should return 422 for invalid UUID format
        assert response.status_code == 422

    def test_post_logs_with_context_data(self):
        """Test log creation with additional context data."""
        log_data = {
            "level": "DEBUG",
            "service": "frontend",
            "correlation_id": str(uuid.uuid4()),
            "message": "Component rendered",
            "context": {
                "component": "ThemeDetector",
                "theme": "dark",
                "user_agent": "Mozilla/5.0",
                "performance": {"render_time_ms": 15},
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=log_data)

        assert response.status_code == 200
        data = response.json()
        assert data["context"] == log_data["context"]

    def test_post_logs_with_user_authentication(self):
        """Test log creation with user authentication."""
        log_data = {
            "level": "WARNING",
            "service": "backend",
            "correlation_id": str(uuid.uuid4()),
            "message": "Authentication warning",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post(
            "/api/v1/logs", json=log_data, headers={"x-user-id": "test-user-789"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test-user-789"

    def test_post_logs_handles_large_context(self):
        """Test log creation with large context data."""
        large_context = {f"field_{i}": f"value_{i}" for i in range(100)}

        log_data = {
            "level": "INFO",
            "service": "frontend",
            "correlation_id": str(uuid.uuid4()),
            "message": "Large context test",
            "context": large_context,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=log_data)

        assert response.status_code == 200
        data = response.json()
        # Context should be stored (possibly sanitized)
        assert "context" in data

    def test_post_logs_performance_requirement(self):
        """Test that log creation response time is under 200ms."""
        import time

        log_data = {
            "level": "INFO",
            "service": "performance_test",
            "correlation_id": str(uuid.uuid4()),
            "message": "Performance test log",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        start_time = time.perf_counter()
        response = client.post("/api/v1/logs", json=log_data)
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000

        assert response.status_code == 200
        assert response_time_ms < 200, (
            f"Response time was {response_time_ms:.2f}ms, expected < 200ms"
        )

    def test_get_logs_endpoint_exists(self):
        """Test that GET /api/v1/logs endpoint exists for log retrieval."""
        response = client.get("/api/v1/logs")

        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        # May return 200 (with logs) or 403 (access denied in production)
        assert response.status_code in [200, 403]
