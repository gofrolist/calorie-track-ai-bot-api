"""
Utility modules for the calorie tracking application.
"""

from .error_handling import (
    handle_api_errors,
    validate_user_authentication,
    validate_uuid_format,
)

__all__ = [
    "handle_api_errors",
    "validate_user_authentication",
    "validate_uuid_format",
]
