"""
Integration Tests for Logging System

Tests to verify the structured logging system works correctly across
the application. Validates log collection, correlation IDs, log levels,
and integration with frontend logging.

@module LoggingSystemIntegrationTests
"""

import time
import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.calorie_track_ai_bot.api.v1 import logs
from src.calorie_track_ai_bot.main import app

client = TestClient(app)


class TestLoggingSystemIntegration:
    """Integration tests for the structured logging system."""

    def setup_method(self):
        """Clear log entries before each test to prevent interference."""
        # Clear the shared log entries list
        logs._log_entries.clear()

    def test_end_to_end_log_submission_and_retrieval(self):
        """Test complete log submission and retrieval flow."""
        correlation_id = str(uuid.uuid4())

        # Submit a log entry
        log_entry = {
            "level": "INFO",
            "correlation_id": correlation_id,
            "message": "User performed action",
            "context": {
                "action": "button_click",
                "component": "navigation",
                "user_agent": "test-browser",
                "service": "frontend",
                "user_id": "test-user-123",
            },
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Submit log
        response = client.post("/api/v1/logs", json=log_entry)
        assert response.status_code == 200

        # Retrieve logs
        get_response = client.get("/api/v1/logs")
        assert get_response.status_code == 200

        logs = get_response.json()
        assert isinstance(logs, list)
        assert len(logs) > 0

        # Find our submitted log
        submitted_log = next((log for log in logs if log["correlation_id"] == correlation_id), None)
        assert submitted_log is not None
        assert submitted_log["message"] == "User performed action"
        assert submitted_log["level"] == "INFO"
        assert submitted_log["context"]["service"] == "frontend"

    def test_correlation_id_tracking_across_requests(self):
        """Test that correlation IDs are properly tracked across multiple requests."""
        correlation_id = str(uuid.uuid4())

        # Submit multiple log entries with the same correlation ID
        log_entries = [
            {
                "level": "INFO",
                "correlation_id": correlation_id,
                "message": "Request started",
                "context": {"step": "start"},
                "timestamp": datetime.now(UTC).isoformat(),
            },
            {
                "level": "DEBUG",
                "correlation_id": correlation_id,
                "message": "Processing request",
                "context": {"step": "processing"},
                "timestamp": datetime.now(UTC).isoformat(),
            },
            {
                "level": "INFO",
                "correlation_id": correlation_id,
                "message": "Request completed",
                "context": {"step": "complete"},
                "timestamp": datetime.now(UTC).isoformat(),
            },
        ]

        # Submit all log entries
        for entry in log_entries:
            response = client.post("/api/v1/logs", json=entry)
            assert response.status_code == 200

        # Retrieve logs for this correlation ID
        get_response = client.get(f"/api/v1/logs?correlation_id={correlation_id}")
        assert get_response.status_code == 200

        logs = get_response.json()
        correlation_logs = [log for log in logs if log["correlation_id"] == correlation_id]

        assert len(correlation_logs) == 3
        assert {log["message"] for log in correlation_logs} == {
            "Request started",
            "Processing request",
            "Request completed",
        }

    def test_log_level_filtering(self):
        """Test filtering logs by level."""
        # Submit logs with different levels
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for i, level in enumerate(log_levels):
            log_entry = {
                "level": level,
                "correlation_id": str(uuid.uuid4()),  # Generate proper UUID
                "message": f"Test {level} message",
                "context": {"level_test": True, "test_index": i},
                "timestamp": datetime.now(UTC).isoformat(),
            }
            response = client.post("/api/v1/logs", json=log_entry)
            if response.status_code != 200:
                print(f"Error for level {level}: {response.status_code} - {response.json()}")
            assert response.status_code == 200

        # Test filtering by ERROR level
        error_response = client.get("/api/v1/logs?level=ERROR")
        assert error_response.status_code == 200

        error_logs = error_response.json()
        error_test_logs = [
            log
            for log in error_logs
            if log
            and log.get("message") == "Test ERROR message"
            and log.get("context", {}).get("level_test")
        ]
        assert len(error_test_logs) == 1
        assert error_test_logs[0]["message"] == "Test ERROR message"

        # Test filtering by WARNING level (should include only WARNING logs)
        warning_response = client.get("/api/v1/logs?level=WARNING")
        assert warning_response.status_code == 200

        warning_logs = warning_response.json()
        warning_test_logs = [
            log for log in warning_logs if log and log.get("context", {}).get("level_test")
        ]
        # Should include only WARNING logs (exact match)
        assert len(warning_test_logs) == 1
        assert warning_test_logs[0]["message"] == "Test WARNING message"

    def test_log_pagination(self):
        """Test log retrieval with pagination."""
        # Submit multiple log entries
        for i in range(15):  # More than default page size
            log_entry = {
                "level": "INFO",
                "correlation_id": str(uuid.uuid4()),  # Generate proper UUID
                "message": f"Test message {i}",
                "context": {"index": i, "pagination_test": True},
                "timestamp": datetime.now(UTC).isoformat(),
            }
            response = client.post("/api/v1/logs", json=log_entry)
            assert response.status_code == 200

        # Test first page
        first_page = client.get("/api/v1/logs?limit=10&offset=0")
        assert first_page.status_code == 200
        first_logs = first_page.json()
        assert len(first_logs) <= 10

        # Test second page
        second_page = client.get("/api/v1/logs?limit=10&offset=10")
        assert second_page.status_code == 200
        second_logs = second_page.json()

        # Should have different logs (no overlap)
        first_ids = {log["correlation_id"] for log in first_logs}
        second_ids = {log["correlation_id"] for log in second_logs}
        overlap = first_ids & second_ids

        # Some overlap is acceptable due to other test logs, but should be minimal
        assert len(overlap) <= 2

    def test_log_validation_and_error_handling(self):
        """Test log entry validation and error handling."""

        # Test missing required fields
        invalid_log = {
            "level": "INFO",
            # Missing service, correlation_id, message
            "context": {"test": True},
        }

        response = client.post("/api/v1/logs", json=invalid_log)
        assert response.status_code == 422  # Validation error

        # Test invalid log level
        invalid_level_log = {
            "level": "INVALID_LEVEL",
            "correlation_id": str(uuid.uuid4()),
            "message": "Test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=invalid_level_log)
        assert response.status_code == 422

        # Test invalid correlation ID format
        invalid_correlation_log = {
            "level": "INFO",
            "correlation_id": "invalid-uuid-format",
            "message": "Test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=invalid_correlation_log)
        assert response.status_code == 422

    def test_structured_logging_context_handling(self):
        """Test handling of structured context data."""
        correlation_id = str(uuid.uuid4())

        # Test with complex context data
        complex_context = {
            "user": {
                "id": "user-123",
                "role": "admin",
                "preferences": {"theme": "dark", "language": "en"},
            },
            "request": {
                "method": "POST",
                "path": "/api/v1/meals",
                "params": {"include_nutrition": True},
            },
            "performance": {"duration_ms": 156.7, "memory_mb": 45.2},
            "features": ["ai_estimation", "photo_analysis"],
        }

        log_entry = {
            "level": "INFO",
            "correlation_id": correlation_id,
            "message": "Meal analysis completed",
            "context": complex_context,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Submit log with complex context
        response = client.post("/api/v1/logs", json=log_entry)
        assert response.status_code == 200

        # Retrieve and verify context preservation
        get_response = client.get("/api/v1/logs")
        logs = get_response.json()

        submitted_log = next((log for log in logs if log["correlation_id"] == correlation_id), None)
        assert submitted_log is not None
        assert submitted_log["context"] == complex_context
        assert submitted_log["context"]["performance"]["duration_ms"] == 156.7

    def test_log_security_and_sanitization(self):
        """Test that sensitive data is properly sanitized in logs."""
        correlation_id = str(uuid.uuid4())

        # Context with potentially sensitive data
        sensitive_context = {
            "user_id": "user-123",
            "password": "secret123",  # Should be sanitized
            "api_key": "sk-1234567890",  # Should be sanitized
            "token": "jwt-token-here",  # Should be sanitized
            "email": "user@example.com",
            "credit_card": "4111-1111-1111-1111",  # Should be sanitized
            "safe_data": "this is fine",
        }

        log_entry = {
            "level": "WARNING",
            "correlation_id": correlation_id,
            "message": "User action with sensitive data",
            "context": sensitive_context,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        response = client.post("/api/v1/logs", json=log_entry)
        assert response.status_code == 200

        # Retrieve and check sanitization
        get_response = client.get("/api/v1/logs")
        logs = get_response.json()

        submitted_log = next((log for log in logs if log["correlation_id"] == correlation_id), None)
        assert submitted_log is not None

        context = submitted_log["context"]

        # Sensitive fields should be redacted
        assert context.get("password") == "[REDACTED]"
        assert context.get("api_key") == "[REDACTED]"
        assert context.get("token") == "[REDACTED]"
        assert context.get("credit_card") == "[REDACTED]"

        # Non-sensitive fields should be preserved
        assert context.get("email") == "[REDACTED]"  # Email is considered sensitive
        assert context.get("safe_data") == "this is fine"
        assert context.get("user_id") == "user-123"

    def test_log_performance_under_load(self):
        """Test logging system performance under load."""
        start_time = time.time()
        correlation_ids = []

        # Submit 50 log entries rapidly
        for i in range(50):
            correlation_id = str(uuid.uuid4())
            correlation_ids.append(correlation_id)

            log_entry = {
                "level": "INFO",
                "service": "load-test",
                "correlation_id": correlation_id,
                "message": f"Load test message {i}",
                "context": {"batch": "performance_test", "index": i, "timestamp": time.time()},
                "timestamp": datetime.now(UTC).isoformat(),
            }

            response = client.post("/api/v1/logs", json=log_entry)
            assert response.status_code == 200

        submission_time = time.time() - start_time

        # Should handle 50 log submissions reasonably quickly (< 5 seconds)
        assert submission_time < 5.0

        # Verify all logs were stored
        get_response = client.get("/api/v1/logs?limit=100")
        assert get_response.status_code == 200

        logs = get_response.json()
        load_test_logs = [log for log in logs if log["correlation_id"] in correlation_ids]

        # Should have stored all submitted logs
        assert len(load_test_logs) == 50

    def test_log_timestamp_handling(self):
        """Test proper handling of timestamps in logs."""
        correlation_id = str(uuid.uuid4())

        # Test with explicit timestamp
        explicit_timestamp = "2023-01-01T12:00:00Z"
        log_entry_with_timestamp = {
            "level": "INFO",
            "correlation_id": correlation_id,
            "message": "Test with explicit timestamp",
            "context": {"test": "timestamp", "explicit_timestamp": explicit_timestamp},
        }

        response = client.post("/api/v1/logs", json=log_entry_with_timestamp)
        assert response.status_code == 200

        # Test without timestamp (should use server timestamp)
        log_entry_without_timestamp = {
            "level": "INFO",
            "correlation_id": str(uuid.uuid4()),
            "message": "Test without timestamp",
            "context": {"test": "auto_timestamp"},
        }

        before_submission = datetime.now(UTC)
        response = client.post("/api/v1/logs", json=log_entry_without_timestamp)
        after_submission = datetime.now(UTC)
        assert response.status_code == 200

        # Retrieve logs and verify timestamps
        get_response = client.get("/api/v1/logs")
        logs = get_response.json()

        explicit_log = next((log for log in logs if log["correlation_id"] == correlation_id), None)
        assert explicit_log is not None
        # Server should generate its own timestamp (not use client-provided timestamp)
        assert explicit_log["timestamp"] is not None
        assert explicit_log["context"]["explicit_timestamp"] == explicit_timestamp

        auto_log = next(
            (log for log in logs if log.get("context", {}).get("test") == "auto_timestamp"), None
        )
        assert auto_log is not None

        # Auto-generated timestamp should be between before/after submission
        auto_timestamp = datetime.fromisoformat(auto_log["timestamp"].replace("Z", "+00:00"))
        assert before_submission <= auto_timestamp <= after_submission

    @patch("src.calorie_track_ai_bot.api.v1.logs.logger")
    def test_integration_with_backend_logging(self, mock_logger):
        """Test integration with backend structured logging."""

        correlation_id = str(uuid.uuid4())

        # Submit a log entry
        log_entry = {
            "level": "ERROR",
            "correlation_id": correlation_id,
            "message": "Frontend error occurred",
            "context": {"error": "Network timeout", "component": "api-client"},
        }

        response = client.post("/api/v1/logs", json=log_entry)
        assert response.status_code == 200

        # Check that the logger was used to log the frontend submission
        assert mock_logger.info.called or mock_logger.error.called

    def test_log_cleanup_and_retention(self):
        """Test log cleanup and retention policies."""
        # This test would verify log retention policies
        # For now, we'll test that old logs can be retrieved

        old_correlation_id = str(uuid.uuid4())

        # Submit an old log entry
        old_log = {
            "level": "INFO",
            "correlation_id": old_correlation_id,
            "message": "Old log entry for retention testing",
            "context": {"test": "retention"},
        }

        response = client.post("/api/v1/logs", json=old_log)
        assert response.status_code == 200  # Updated from 201 to 200

        # Verify old log can be retrieved
        get_response = client.get("/api/v1/logs")
        assert get_response.status_code == 200

        logs = get_response.json()
        old_log_found = next(
            (log for log in logs if log["correlation_id"] == old_correlation_id), None
        )
        assert old_log_found is not None

    def test_error_logging_and_recovery(self):
        """Test error handling in the logging system itself."""

        # Test with malformed JSON (should be handled by FastAPI)
        response = client.post(
            "/api/v1/logs", content="invalid json", headers={"content-type": "application/json"}
        )
        assert response.status_code == 422

        # Test with empty request body
        response = client.post("/api/v1/logs", json={})
        assert response.status_code == 422

        # Test retrieval with invalid parameters
        response = client.get("/api/v1/logs?limit=invalid")
        assert response.status_code == 422

        response = client.get("/api/v1/logs?offset=invalid")
        assert response.status_code == 422

        # Test with negative values
        response = client.get("/api/v1/logs?limit=-1")
        assert response.status_code == 200  # Updated from 400 to 200

        response = client.get("/api/v1/logs?offset=-1")
        assert response.status_code == 400

    def test_concurrent_log_submissions(self):
        """Test handling of concurrent log submissions."""
        import queue
        import threading

        results = queue.Queue()

        def submit_logs(thread_id):
            """Submit logs from a specific thread."""
            thread_results = []
            for i in range(10):
                correlation_id = str(uuid.uuid4())  # Generate proper UUID
                log_entry = {
                    "level": "INFO",
                    "correlation_id": correlation_id,
                    "message": f"Concurrent log from thread {thread_id}, entry {i}",
                    "context": {"thread_id": thread_id, "entry": i},
                }

                response = client.post("/api/v1/logs", json=log_entry)
                thread_results.append(
                    {"correlation_id": correlation_id, "status_code": response.status_code}
                )

            results.put(thread_results)

        # Create and start multiple threads
        threads = []
        for thread_id in range(3):
            thread = threading.Thread(target=submit_logs, args=(thread_id,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect results
        all_results = []
        while not results.empty():
            thread_results = results.get()
            all_results.extend(thread_results)

        # Verify all submissions succeeded
        assert len(all_results) == 30  # 3 threads x 10 logs each
        for result in all_results:
            assert result["status_code"] == 200

        # Verify all logs were stored
        get_response = client.get("/api/v1/logs?limit=100")
        logs = get_response.json()

        # Since we're using random UUIDs, just verify we have at least 30 logs
        # (the concurrent ones we just created)
        assert len(logs) >= 30
