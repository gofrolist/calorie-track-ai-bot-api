"""
Error handling utilities for API endpoints.

This module provides common error handling patterns to reduce code duplication
across API endpoints.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from fastapi import HTTPException

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_api_errors(operation_name: str = "operation", log_level: int = logging.ERROR):
    """
    Decorator to handle common API errors with consistent logging and HTTP responses.

    Args:
        operation_name: Name of the operation for logging purposes
        log_level: Logging level for errors (default: ERROR)

    Returns:
        Decorated function with error handling
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except Exception as e:
                # Log the error with context
                logger.log(log_level, f"Error in {operation_name}: {e}", exc_info=True)
                # Convert to HTTP 500 error
                raise HTTPException(status_code=500, detail=str(e)) from e

        return wrapper  # type: ignore

    return decorator


def handle_database_errors(
    operation_name: str = "database operation", not_found_message: str = "Resource not found"
):
    """
    Decorator to handle database-specific errors.

    Args:
        operation_name: Name of the operation for logging
        not_found_message: Message to return for 404 errors

    Returns:
        Decorated function with database error handling
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                error_str = str(e)

                # Handle specific database errors
                if "Could not find the table" in error_str:
                    logger.warning(f"Database table not found in {operation_name}: {e}")
                    raise HTTPException(status_code=404, detail=not_found_message) from e

                # Handle other database errors
                logger.error(f"Database error in {operation_name}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e)) from e

        return wrapper  # type: ignore

    return decorator


def validate_user_authentication(request) -> str:
    """
    Extract and validate user ID from request headers.

    Args:
        request: FastAPI Request object

    Returns:
        User ID string

    Raises:
        HTTPException: If user ID is missing or invalid
    """
    telegram_user_id = request.headers.get("x-user-id")
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return telegram_user_id


def validate_uuid_format(id_value: str, field_name: str = "ID") -> None:
    """
    Validate that a string is a valid UUID format.

    Args:
        id_value: String to validate
        field_name: Name of the field for error messages

    Raises:
        HTTPException: If UUID format is invalid
    """
    from uuid import UUID

    try:
        UUID(id_value)
    except ValueError:
        raise HTTPException(
            status_code=422, detail=f"Invalid {field_name.lower()} format"
        ) from None
