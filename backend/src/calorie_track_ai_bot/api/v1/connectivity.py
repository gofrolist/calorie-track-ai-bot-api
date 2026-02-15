"""
Health connectivity endpoints for frontend-backend integration.
"""

import time
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, HTTPException, Request

from ...schemas import ConnectionStatus, ConnectivityResponse
from ...services.config import APP_ENV

router = APIRouter()

logger = structlog.get_logger(__name__)

API_VERSION = "1.0.0"


def _get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID for request tracking."""
    return (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )


def _is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is a valid UUID format."""
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


async def _perform_health_checks() -> tuple[bool, dict]:
    """
    Perform health checks including a real database ping.

    Returns:
        tuple: (is_healthy, check_details)
    """
    checks = {}
    is_healthy = True

    # Database connectivity check (only if pool already initialized)
    try:
        from ...services import database

        if database._pool is not None:
            db_start = time.perf_counter()
            async with database._pool.connection() as conn:
                cur = await conn.execute("SELECT 1")
                await cur.fetchone()
            db_time_ms = (time.perf_counter() - db_start) * 1000
            checks["database"] = {"status": "available", "response_time_ms": round(db_time_ms, 2)}
        else:
            checks["database"] = {"status": "not_initialized"}
    except Exception:
        checks["database"] = {"status": "unavailable"}

    checks["application"] = {"status": "healthy"}

    return is_healthy, checks


@router.get("/connectivity", response_model=ConnectivityResponse)
async def get_connectivity_status(request: Request) -> ConnectivityResponse:
    """
    Check connectivity between frontend and backend.

    Performs health checks on backend services and returns status with timing
    and correlation information for distributed tracing.

    Returns:
        ConnectivityResponse: Status with timing and correlation information

    Raises:
        HTTPException: 503 if backend services are unhealthy
    """
    start_time = time.perf_counter()

    correlation_id_str = _get_correlation_id(request)
    correlation_id = (
        uuid.UUID(correlation_id_str) if _is_valid_uuid(correlation_id_str) else uuid.uuid4()
    )

    try:
        is_healthy, check_details = await _perform_health_checks()

        response_time_ms = (time.perf_counter() - start_time) * 1000

        status = ConnectionStatus.connected if is_healthy else ConnectionStatus.error

        response = ConnectivityResponse(
            status=status,
            services={
                "api_version": API_VERSION,
                "environment": APP_ENV,
                "checks_performed": list(check_details.keys()),
                "health_details": check_details,
            },
            response_time_ms=response_time_ms,
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
        )

        if not is_healthy:
            raise HTTPException(status_code=503, detail=response.model_dump(mode="json"))

        return response

    except HTTPException:
        raise

    except Exception as e:
        response_time_ms = (time.perf_counter() - start_time) * 1000

        logger.error(
            "Connectivity check failed",
            correlation_id=str(correlation_id),
            error=str(e),
            response_time_ms=response_time_ms,
        )

        response = ConnectivityResponse(
            status=ConnectionStatus.error,
            services={
                "api_version": API_VERSION,
                "environment": APP_ENV,
                "error": "Internal server error",
            },
            response_time_ms=response_time_ms,
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
        )

        raise HTTPException(status_code=500, detail=response.model_dump(mode="json")) from e
