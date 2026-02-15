"""
Development environment endpoints for local development tools and status.
"""

import os
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from ...schemas import DevelopmentEnvironment
from ...services.config import APP_ENV
from ..v1.config import get_current_user

router = APIRouter()

logger = structlog.get_logger(__name__)

DEV_ENDPOINTS_ENABLED = os.getenv("DEV_ENDPOINTS_ENABLED", "true").lower() == "true"

# Environment configuration
DEVELOPMENT_CONFIG = {
    "database_url": os.getenv("DATABASE_URL", "postgresql://localhost:5432/neondb"),
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "storage_endpoint": os.getenv("STORAGE_ENDPOINT", "http://localhost:9000"),
    "frontend_port": int(os.getenv("FRONTEND_PORT", "5173")),
    "backend_port": int(os.getenv("BACKEND_PORT", "8000")),
}

STABLE_ENVIRONMENT_ID = "12345678-1234-5678-9abc-123456789abc"


def _get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request headers."""
    return (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )


def _check_dev_endpoints_access(user_id: str) -> bool:
    """Check if development endpoints are accessible."""
    if APP_ENV == "production" and not DEV_ENDPOINTS_ENABLED:
        logger.warning(
            "Development endpoints access attempted in production",
            environment=APP_ENV,
        )
        return False
    return True


@router.get("/dev/environment", response_model=DevelopmentEnvironment)
async def get_development_environment(
    request: Request, user_id: str = Depends(get_current_user)
) -> DevelopmentEnvironment:
    """
    Get current development environment configuration.

    Returns:
        DevelopmentEnvironment: Current development environment settings

    Raises:
        HTTPException: 403 for access denied, 500 for server errors
    """
    correlation_id = _get_correlation_id(request)

    if not _check_dev_endpoints_access(user_id):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_denied",
                "message": "Development endpoints are not available",
                "correlation_id": correlation_id,
            },
        )

    try:
        now = datetime.now(UTC)

        dev_env = DevelopmentEnvironment(
            id=uuid.UUID(STABLE_ENVIRONMENT_ID),
            name=f"{APP_ENV}-development" if APP_ENV != "production" else "production-limited",
            frontend_port=DEVELOPMENT_CONFIG["frontend_port"],
            backend_port=DEVELOPMENT_CONFIG["backend_port"],
            supabase_db_url=DEVELOPMENT_CONFIG["database_url"],
            supabase_db_password="",
            redis_url=DEVELOPMENT_CONFIG["redis_url"],
            storage_endpoint=DEVELOPMENT_CONFIG["storage_endpoint"],
            cors_origins=[
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]
            if APP_ENV != "production"
            else [],
            log_level="DEBUG" if APP_ENV != "production" else "INFO",
            hot_reload=APP_ENV != "production",
            supabase_cli_version="1.0.0",
            created_at=now,
            updated_at=now,
        )

        return dev_env

    except Exception as e:
        logger.error(
            "Failed to get development environment",
            error=str(e),
            correlation_id=correlation_id,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "environment_retrieval_failed",
                "message": "Internal server error occurred",
                "correlation_id": correlation_id,
            },
        ) from e


@router.get("/dev/db/status")
async def get_db_status(request: Request, user_id: str = Depends(get_current_user)) -> dict:
    """Get database connection pool status."""
    correlation_id = _get_correlation_id(request)

    if not _check_dev_endpoints_access(user_id):
        raise HTTPException(
            status_code=403,
            detail={"error": "access_denied", "correlation_id": correlation_id},
        )

    try:
        from ...services.database import get_pool

        pool = await get_pool()
        async with pool.connection() as conn:
            cur = await conn.execute("SELECT 1")
            await cur.fetchone()

        now = datetime.now(UTC)
        return {
            "status": "running",
            "database_url": DEVELOPMENT_CONFIG["database_url"],
            "last_check": now.isoformat(),
        }

    except Exception as e:
        logger.error(
            "Database status check failed",
            error=str(e),
            correlation_id=correlation_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "db_status_failed", "correlation_id": correlation_id},
        ) from e
