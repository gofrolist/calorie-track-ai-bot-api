"""Shared FastAPI dependencies for API v1 route handlers.

Provides reusable dependency functions for authentication and user resolution.
"""

from fastapi import HTTPException, Request

from ...services.db import resolve_user_id
from ...utils.error_handling import validate_user_authentication


async def get_authenticated_user_id(request: Request) -> str:
    """Authenticate the request and resolve the telegram user to an internal user ID.

    Combines user authentication (x-user-id header extraction) with database
    user ID resolution into a single reusable dependency.

    Args:
        request: FastAPI Request object

    Returns:
        Internal database user ID (UUID string)

    Raises:
        HTTPException 401: If x-user-id header is missing
        HTTPException 404: If user not found in database
    """
    telegram_user_id = validate_user_authentication(request)
    internal_user_id = await resolve_user_id(telegram_user_id)
    if not internal_user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return internal_user_id
