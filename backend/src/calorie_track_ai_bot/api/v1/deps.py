"""Shared FastAPI dependencies for API v1 route handlers.

Provides reusable dependency functions for authentication and user resolution.
"""

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException, Request

from ...services.db import resolve_user_id


def get_telegram_user_id(request: Request) -> str:
    """Extract and validate telegram user ID from x-user-id header.

    Use as a FastAPI dependency: Depends(get_telegram_user_id)
    """
    telegram_user_id = request.headers.get("x-user-id")
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="Missing x-user-id header")
    return telegram_user_id


async def get_authenticated_user_id(request: Request) -> str:
    """Authenticate the request and resolve the telegram user to an internal user ID.

    Combines user authentication (x-user-id header extraction) with database
    user ID resolution into a single reusable dependency.
    """
    telegram_user_id = get_telegram_user_id(request)
    internal_user_id = await resolve_user_id(telegram_user_id)
    if not internal_user_id:
        raise HTTPException(status_code=404, detail="User not found")
    return internal_user_id


def get_user_timezone(request: Request) -> str:
    """Return the client's IANA time zone from the x-timezone header.

    Meals are bucketed into the user's local calendar days with it. Falls back to
    UTC when the header is missing or names an unknown zone.
    Use as a FastAPI dependency: Depends(get_user_timezone)
    """
    tz_name = (request.headers.get("x-timezone") or "").strip()
    if not tz_name:
        return "UTC"
    try:
        ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return "UTC"
    return tz_name
