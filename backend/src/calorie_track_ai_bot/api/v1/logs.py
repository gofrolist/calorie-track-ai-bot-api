"""
Logging endpoints for structured log collection and monitoring.
"""

import hashlib
import hmac
import os
import uuid
from datetime import UTC, datetime
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from ...schemas import LogEntry, LogEntryCreate, LogLevel
from ...services.config import APP_ENV
from ..v1.config import get_current_user

router = APIRouter()

# Initialize structured logger
logger = structlog.get_logger(__name__)

# Security for log access
security = HTTPBearer(auto_error=False)

# Secret key for secure user ID hashing (in production, load from environment)
LOG_HASH_SECRET = os.getenv("LOG_HASH_SECRET", "default-dev-secret-change-in-production")

# In-memory log storage for development
# In production, this would be replaced with proper log aggregation (ELK, Splunk, etc.)
_log_entries: list[LogEntry] = []

# Log level to logger method mapping for cleaner code
LOG_LEVEL_METHODS = {
    LogLevel.DEBUG: lambda msg, **ctx: logger.debug(msg, **ctx),
    LogLevel.INFO: lambda msg, **ctx: logger.info(msg, **ctx),
    LogLevel.WARNING: lambda msg, **ctx: logger.warning(msg, **ctx),
    LogLevel.ERROR: lambda msg, **ctx: logger.error(msg, **ctx),
    LogLevel.CRITICAL: lambda msg, **ctx: logger.critical(msg, **ctx),
}

# Sensitive fields that should be redacted from logs
SENSITIVE_FIELDS = {
    "password",
    "token",
    "secret",
    "key",
    "auth",
    "credential",
    "ssn",
    "social_security",
    "credit_card",
    "email",
    "phone",
    "api_key",
    "access_token",
    "refresh_token",
    "session_id",
}


def _get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request headers."""
    return (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )


def _secure_hash_user_id(user_id: str) -> str:
    """
    Create a secure, consistent hash of user ID for privacy-safe logging.

    Args:
        user_id: User ID to hash

    Returns:
        str: Secure hash suitable for logging
    """
    return hmac.new(LOG_HASH_SECRET.encode(), user_id.encode(), hashlib.sha256).hexdigest()[
        :8
    ]  # Use first 8 characters for brevity


def _sanitize_context(context: dict[str, Any]) -> dict[str, Any]:
    """
    Sanitize context data by redacting sensitive information.

    Args:
        context: Context dictionary to sanitize

    Returns:
        Dict[str, Any]: Sanitized context with sensitive fields redacted
    """
    if not context:
        return {}

    sanitized = {}
    for key, value in context.items():
        # Check if key contains sensitive field names
        key_lower = key.lower()
        is_sensitive = any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS)

        if is_sensitive:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = _sanitize_context(value)
        elif isinstance(value, list):
            # Sanitize list items if they're dictionaries
            sanitized[key] = [
                _sanitize_context(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def _check_log_access_permission(user_id: str) -> bool:
    """
    Check if user has permission to access logs.

    Args:
        user_id: User ID to check permissions for

    Returns:
        bool: True if user has log access permission

    Note:
        In production, this would check against a proper authorization system.
        For development, we allow access but log the attempt.
    """
    if APP_ENV == "production":
        # In production, implement proper RBAC/permissions checking
        # For now, return False to be restrictive
        logger.warning(
            "Log access attempted in production", user_id_hash=_secure_hash_user_id(user_id)
        )
        return False

    # In development, allow access but log it
    logger.info("Log access granted for development", user_id_hash=_secure_hash_user_id(user_id))
    return True


@router.post("/logs", response_model=LogEntry)
async def create_log_entry(
    log_data: LogEntryCreate, request: Request, user_id: str = Depends(get_current_user)
) -> LogEntry:
    """
    Create a new log entry for structured logging.

    Args:
        log_data: Log entry data
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        LogEntry: Created log entry with ID and timestamp

    Raises:
        HTTPException: 400 for validation errors, 500 for server errors
    """
    correlation_id = _get_correlation_id(request)

    try:
        # Sanitize context data to remove sensitive information
        sanitized_context = _sanitize_context(log_data.context) if log_data.context else None

        # Create log entry with metadata
        now = datetime.now(UTC)
        log_entry = LogEntry(
            id=uuid.uuid4(),
            timestamp=now,
            level=log_data.level,
            message=log_data.message,
            correlation_id=log_data.correlation_id or uuid.UUID(correlation_id),
            module=log_data.module,
            function=log_data.function,
            user_id=user_id,  # Add user context
            request_id=correlation_id,
            context=sanitized_context,
            error_details=None,  # Will be populated for error logs
        )

        # Store log entry (in production, send to log aggregation system)
        _log_entries.append(log_entry)

        # Also log to structured logger for development
        secure_user_hash = _secure_hash_user_id(user_id)
        log_context = {
            "log_id": str(log_entry.id),
            "user_id_hash": secure_user_hash,
            "correlation_id": correlation_id,
            "module": log_data.module,
            "function": log_data.function,
        }

        # Add sanitized context to logging context
        if sanitized_context:
            log_context.update(sanitized_context)

        # Use mapping for cleaner log level handling
        log_method = LOG_LEVEL_METHODS.get(log_entry.level)
        if log_method:
            log_method(log_data.message, **log_context)
        else:
            # Fallback for unknown log levels
            logger.error(f"Unknown log level: {log_entry.level}", **log_context)

        logger.info(
            "Log entry created",
            log_id=str(log_entry.id),
            level=log_entry.level.value,
            user_id_hash=secure_user_hash,
            correlation_id=correlation_id,
        )

        return log_entry

    except Exception as e:
        secure_user_hash = _secure_hash_user_id(user_id)
        logger.error(
            "Failed to create log entry",
            error=str(e),
            error_type=type(e).__name__,
            user_id_hash=secure_user_hash,
            correlation_id=correlation_id,
        )

        # In production, consider implementing circuit breaker or backoff
        # if log failures are frequent to prevent cascading failures

        raise HTTPException(
            status_code=500,
            detail={
                "error": "log_creation_failed",
                "message": "Failed to create log entry",
                "correlation_id": correlation_id,
            },
        ) from e


@router.get("/logs", response_model=list[LogEntry])
async def get_log_entries(
    request: Request,
    user_id: str = Depends(get_current_user),
    level: LogLevel | None = None,
    correlation_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[LogEntry]:
    """
    Retrieve log entries (development/debugging endpoint with access control).

    Args:
        request: FastAPI request object
        user_id: Authenticated user ID
        level: Optional log level filter
        correlation_id: Optional correlation ID filter
        limit: Maximum number of entries to return (max 1000)
        offset: Number of entries to skip for pagination

    Returns:
        list[LogEntry]: List of log entries

    Raises:
        HTTPException: 403 for access denied, 400 for invalid parameters, 500 for server errors

    Note:
        This endpoint is restricted and requires appropriate permissions.
        In production, use proper log aggregation tools with RBAC.
    """
    request_correlation_id = _get_correlation_id(request)
    secure_user_hash = _secure_hash_user_id(user_id)

    # Check access permissions
    if not _check_log_access_permission(user_id):
        logger.warning(
            "Log access denied",
            user_id_hash=secure_user_hash,
            correlation_id=request_correlation_id,
            reason="insufficient_permissions",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_denied",
                "message": "Insufficient permissions to access logs",
                "correlation_id": request_correlation_id,
            },
        )

    # Validate parameters
    if limit > 1000:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_parameter",
                "message": "Limit cannot exceed 1000 entries",
                "correlation_id": request_correlation_id,
            },
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_parameter",
                "message": "Offset cannot be negative",
                "correlation_id": request_correlation_id,
            },
        )

    logger.info(
        "Log entries requested",
        user_id_hash=secure_user_hash,
        level_filter=level.value if level else None,
        correlation_filter=correlation_id,
        limit=limit,
        offset=offset,
        correlation_id=request_correlation_id,
    )

    try:
        # More efficient filtering approach
        # In production, this would use indexed queries in a proper database

        # Apply filters
        filtered_logs = _log_entries.copy()

        # Apply level filter
        if level:
            filtered_logs = [entry for entry in filtered_logs if entry.level == level]

        # Apply correlation_id filter
        if correlation_id:
            filtered_logs = [
                entry for entry in filtered_logs if str(entry.correlation_id) == correlation_id
            ]

        # Sort by timestamp (newest first) - in production, would be indexed
        filtered_logs.sort(key=lambda x: x.timestamp, reverse=True)

        # Apply pagination
        total_count = len(filtered_logs)
        paginated_logs = filtered_logs[offset : offset + limit]

        logger.info(
            "Log entries retrieved",
            user_id_hash=secure_user_hash,
            returned_count=len(paginated_logs),
            total_filtered=total_count,
            total_logs=len(_log_entries),
            correlation_id=request_correlation_id,
        )

        return paginated_logs

    except Exception as e:
        logger.error(
            "Failed to retrieve log entries",
            error=str(e),
            error_type=type(e).__name__,
            user_id_hash=secure_user_hash,
            correlation_id=request_correlation_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "log_retrieval_failed",
                "message": "Failed to retrieve log entries",
                "correlation_id": request_correlation_id,
            },
        ) from e
