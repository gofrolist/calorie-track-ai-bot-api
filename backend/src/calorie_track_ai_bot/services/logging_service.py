"""
Structured Logging Service

Service for managing structured logging with correlation IDs, context data,
and integration with external logging systems.
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from ..schemas import LogEntry, LogEntryCreate, LogLevel

logger = logging.getLogger(__name__)


class StructuredLoggingService:
    """Service for structured logging with correlation IDs and context."""

    def __init__(self):
        self._log_entries: list[LogEntry] = []
        self._correlation_context: dict[str, Any] = {}
        self._sensitive_fields = {
            "password",
            "token",
            "key",
            "secret",
            "email",
            "phone",
            "ssn",
            "credit_card",
        }
        self._log_hash_secret = "default-secret-change-in-production"

    def _generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    def _secure_hash_user_id(self, user_id: str) -> str:
        """
        Securely hash user ID for logging.

        Args:
            user_id: User ID to hash

        Returns:
            str: Hashed user ID
        """
        return hmac.new(
            self._log_hash_secret.encode(), user_id.encode(), hashlib.sha256
        ).hexdigest()[:16]

    def _sanitize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Sanitize context data to remove sensitive information.

        Args:
            context: Context data to sanitize

        Returns:
            Dict[str, Any]: Sanitized context data
        """
        if not context:
            return {}

        sanitized = {}
        for key, value in context.items():
            if any(sensitive in key.lower() for sensitive in self._sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_context(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_context(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    async def create_log_entry(
        self,
        level: LogLevel,
        message: str,
        correlation_id: str | None = None,
        user_id: str | None = None,
        context: dict[str, Any] | None = None,
        module: str | None = None,
        function: str | None = None,
    ) -> LogEntry:
        """
        Create a structured log entry.

        Args:
            level: Log level
            message: Log message
            correlation_id: Optional correlation ID
            user_id: Optional user ID
            context: Optional context data
            module: Optional module name
            function: Optional function name

        Returns:
            LogEntry: Created log entry
        """
        if not correlation_id:
            correlation_id = self._generate_correlation_id()

        # Sanitize context data
        sanitized_context = self._sanitize_context(context or {})

        # Create log entry
        log_entry = LogEntry(
            id=uuid.uuid4(),
            timestamp=datetime.now(UTC),
            level=level,
            message=message,
            correlation_id=uuid.UUID(correlation_id),
            module=module,
            function=function,
            user_id=user_id,
            request_id=None,
            context=sanitized_context,
            error_details=None,
        )

        # Store log entry
        self._log_entries.append(log_entry)

        # Log to standard logger
        secure_user_hash = self._secure_hash_user_id(user_id) if user_id else None

        log_data = {
            "log_id": str(log_entry.id),
            "correlation_id": correlation_id,
            "user_id_hash": secure_user_hash,
            "module": module,
            "function": function,
            "context": sanitized_context,
        }

        # Use appropriate log level
        if level == LogLevel.DEBUG:
            logger.debug(message, extra=log_data)
        elif level == LogLevel.INFO:
            logger.info(message, extra=log_data)
        elif level == LogLevel.WARNING:
            logger.warning(message, extra=log_data)
        elif level == LogLevel.ERROR:
            logger.error(message, extra=log_data)
        elif level == LogLevel.CRITICAL:
            logger.critical(message, extra=log_data)

        return log_entry

    async def submit_log_entry(self, log_data: LogEntryCreate) -> LogEntry:
        """
        Submit a log entry from external source (e.g., frontend).

        Args:
            log_data: Log entry data

        Returns:
            LogEntry: Created log entry
        """
        return await self.create_log_entry(
            level=log_data.level,
            message=log_data.message,
            correlation_id=str(log_data.correlation_id) if log_data.correlation_id else None,
            context=log_data.context,
            module=log_data.module,
            function=log_data.function,
        )

    async def get_log_entries(
        self,
        level: LogLevel | None = None,
        correlation_id: str | None = None,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LogEntry]:
        """
        Retrieve log entries with filtering.

        Args:
            level: Optional log level filter
            correlation_id: Optional correlation ID filter
            user_id: Optional user ID filter
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List[LogEntry]: Filtered log entries
        """
        filtered_logs = self._log_entries.copy()

        # Apply filters
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]

        if correlation_id:
            filtered_logs = [
                log for log in filtered_logs if str(log.correlation_id) == correlation_id
            ]

        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]

        # Sort by timestamp (newest first)
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        return filtered_logs[offset : offset + limit]

    def set_correlation_context(self, correlation_id: str, context: dict[str, Any]) -> None:
        """
        Set correlation context for a correlation ID.

        Args:
            correlation_id: Correlation ID
            context: Context data
        """
        self._correlation_context[correlation_id] = context

    def get_correlation_context(self, correlation_id: str) -> dict[str, Any] | None:
        """
        Get correlation context for a correlation ID.

        Args:
            correlation_id: Correlation ID

        Returns:
            Optional[Dict[str, str]]: Correlation context
        """
        return self._correlation_context.get(correlation_id)

    def clear_correlation_context(self, correlation_id: str) -> None:
        """
        Clear correlation context for a correlation ID.

        Args:
            correlation_id: Correlation ID
        """
        self._correlation_context.pop(correlation_id, None)

    def clear_all_logs(self) -> None:
        """Clear all log entries."""
        self._log_entries.clear()
        self._correlation_context.clear()
        logger.info("All log entries and correlation context cleared")

    def get_log_statistics(self) -> dict[str, Any]:
        """
        Get logging statistics.

        Returns:
            Dict[str, Any]: Logging statistics
        """
        total_logs = len(self._log_entries)
        level_counts = {}

        for log in self._log_entries:
            level = log.level.value
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "total_logs": total_logs,
            "level_counts": level_counts,
            "active_correlations": len(self._correlation_context),
            "oldest_log": min(self._log_entries, key=lambda x: x.timestamp).timestamp
            if self._log_entries
            else None,
            "newest_log": max(self._log_entries, key=lambda x: x.timestamp).timestamp
            if self._log_entries
            else None,
        }

    async def export_logs(
        self,
        format: str = "json",
        level: LogLevel | None = None,
        correlation_id: str | None = None,
        user_id: str | None = None,
    ) -> str:
        """
        Export logs in specified format.

        Args:
            format: Export format ("json", "csv")
            level: Optional log level filter
            correlation_id: Optional correlation ID filter
            user_id: Optional user ID filter

        Returns:
            str: Exported logs
        """
        logs = await self.get_log_entries(level, correlation_id, user_id)

        if format == "json":
            return json.dumps([log.model_dump() for log in logs], default=str)
        elif format == "csv":
            # Simple CSV export
            if not logs:
                return ""

            headers = [
                "timestamp",
                "level",
                "message",
                "correlation_id",
                "user_id",
                "module",
                "function",
            ]
            rows = [headers]

            for log in logs:
                row = [
                    log.timestamp.isoformat(),
                    log.level.value,
                    log.message,
                    str(log.correlation_id),
                    log.user_id or "",
                    log.module or "",
                    log.function or "",
                ]
                rows.append(row)

            return "\n".join(",".join(str(cell) for cell in row) for row in rows)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def configure_sensitive_fields(self, fields: list[str]) -> None:
        """
        Configure sensitive fields for redaction.

        Args:
            fields: List of sensitive field names
        """
        self._sensitive_fields = set(fields)
        logger.info(f"Updated sensitive fields: {self._sensitive_fields}")

    def set_log_hash_secret(self, secret: str) -> None:
        """
        Set secret for user ID hashing.

        Args:
            secret: Secret key for hashing
        """
        self._log_hash_secret = secret
        logger.info("Updated log hash secret")


# Global service instance
structured_logging_service = StructuredLoggingService()
