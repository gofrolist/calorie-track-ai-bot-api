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
                raise HTTPException(status_code=500, detail="Internal server error") from e

        return wrapper  # type: ignore

    return decorator
