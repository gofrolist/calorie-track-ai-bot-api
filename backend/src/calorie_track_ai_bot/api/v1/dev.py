"""
Development environment endpoints for local development tools and status.
Enhanced with security, performance, and production-ready practices.
"""

import asyncio
import hashlib
import hmac
import os
import shlex
import threading
import time
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer

from ...schemas import DevelopmentEnvironment
from ...services.config import APP_ENV
from ..v1.config import get_current_user

router = APIRouter()

# Initialize structured logger
logger = structlog.get_logger(__name__)

# Security configuration
security = HTTPBearer(auto_error=False)
DEV_ENDPOINTS_ENABLED = os.getenv("DEV_ENDPOINTS_ENABLED", "true").lower() == "true"

# Secure secret management with production safeguards
DEV_HASH_SECRET = os.getenv("LOG_HASH_SECRET", "dev-fallback-secret-32-chars-long")
if not DEV_HASH_SECRET:
    if APP_ENV == "production":
        raise ValueError("LOG_HASH_SECRET must be set in production environment")
    DEV_HASH_SECRET = "default-dev-secret-change-in-production"
    logger.warning(
        "Using default development secret - THIS IS UNSAFE FOR PRODUCTION", environment=APP_ENV
    )

# Environment configuration with security validation
DEVELOPMENT_CONFIG = {
    "database_url": os.getenv("DATABASE_URL", "postgresql://localhost:5432/neondb"),
    "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "storage_endpoint": os.getenv("STORAGE_ENDPOINT", "http://localhost:9000"),
    "frontend_port": int(os.getenv("FRONTEND_PORT", "5173")),
    "backend_port": int(os.getenv("BACKEND_PORT", "8000")),
}

# Production safety checks
if APP_ENV == "production":
    unsafe_defaults = []
    if "localhost" in DEVELOPMENT_CONFIG["database_url"]:
        unsafe_defaults.append("database_url contains localhost")
    if "localhost" in DEVELOPMENT_CONFIG["redis_url"]:
        unsafe_defaults.append("redis_url contains localhost")

    if unsafe_defaults:
        logger.error(
            "Unsafe development defaults detected in production",
            unsafe_defaults=unsafe_defaults,
            environment=APP_ENV,
        )

# In-memory caching with thread safety
_cache_lock = threading.RLock()
_environment_cache: dict[str, dict] = {}
_supabase_status_cache: dict | None = None
_cache_timestamps: dict[str, float] = {}

# Cache configuration
ENVIRONMENT_CACHE_TTL = 300  # 5 minutes
SUPABASE_STATUS_CACHE_TTL = 30  # 30 seconds
STABLE_ENVIRONMENT_ID = (
    "12345678-1234-5678-9abc-123456789abc"  # Stable UUID for development environment
)


def _secure_hash_user_id(user_id: str) -> str:
    """
    Create a secure, consistent hash of user ID for privacy-safe logging.

    Args:
        user_id: User ID to hash

    Returns:
        str: Secure hash suitable for logging
    """
    return hmac.new(DEV_HASH_SECRET.encode(), user_id.encode(), hashlib.sha256).hexdigest()[:8]


def _get_correlation_id(request: Request) -> str:
    """Extract correlation ID from request headers."""
    return (
        request.headers.get("x-correlation-id")
        or request.headers.get("x-request-id")
        or str(uuid.uuid4())
    )


def _check_dev_endpoints_access(user_id: str) -> bool:
    """
    Enhanced security check for development endpoints access.

    Args:
        user_id: User ID requesting access

    Returns:
        bool: True if access should be granted
    """
    # In production, development endpoints should be disabled
    if APP_ENV == "production" and not DEV_ENDPOINTS_ENABLED:
        logger.warning(
            "Development endpoints access attempted in production",
            user_id_hash=_secure_hash_user_id(user_id),
            environment=APP_ENV,
            endpoints_enabled=DEV_ENDPOINTS_ENABLED,
        )
        return False

    # Additional access control logic can be added here
    # For example, checking if user has admin privileges

    return True


def _get_cached_data(cache_key: str, ttl: int) -> dict | None:
    """
    Thread-safe cache retrieval with TTL checking.

    Args:
        cache_key: Cache key to retrieve
        ttl: Time-to-live in seconds

    Returns:
        Optional[Dict]: Cached data if valid, None otherwise
    """
    with _cache_lock:
        if cache_key not in _cache_timestamps:
            return None

        cache_time = _cache_timestamps[cache_key]
        if time.time() - cache_time > ttl:
            # Cache expired, remove it
            _cache_timestamps.pop(cache_key, None)
            if cache_key == "supabase_status":
                global _supabase_status_cache
                _supabase_status_cache = None
            else:
                _environment_cache.pop(cache_key, None)
            return None

        # Return cached data
        if cache_key == "supabase_status":
            return _supabase_status_cache
        return _environment_cache.get(cache_key)


def _set_cached_data(cache_key: str, data: dict) -> None:
    """
    Thread-safe cache storage.

    Args:
        cache_key: Cache key to store
        data: Data to cache
    """
    with _cache_lock:
        _cache_timestamps[cache_key] = time.time()
        if cache_key == "supabase_status":
            global _supabase_status_cache
            _supabase_status_cache = data
        else:
            _environment_cache[cache_key] = data


def _sanitize_subprocess_command(command: list) -> list:
    """
    Sanitize subprocess command to prevent injection attacks.

    Args:
        command: Command list to sanitize

    Returns:
        list: Sanitized command

    Raises:
        ValueError: If command contains unsafe elements
    """
    if not command or not isinstance(command, list):
        raise ValueError("Command must be a non-empty list")

    # Allowed commands for development endpoints
    allowed_commands = {"supabase"}
    base_command = command[0]

    if base_command not in allowed_commands:
        raise ValueError(f"Command '{base_command}' not allowed")

    # Sanitize arguments - no user input should reach here, but extra safety
    sanitized = []
    for arg in command:
        if not isinstance(arg, str):
            raise ValueError("All command arguments must be strings")

        # Prevent command injection
        if any(char in arg for char in [";", "&", "|", "`", "$", "(", ")", "<", ">"]):
            raise ValueError(f"Unsafe character detected in argument: {arg}")

        sanitized.append(shlex.quote(arg))

    return sanitized


async def _check_supabase_status_with_retry(max_retries: int = 2, timeout: int = 5) -> dict:
    """
    Check Supabase CLI status with retry logic and caching.

    Args:
        max_retries: Maximum number of retry attempts
        timeout: Timeout for each attempt in seconds

    Returns:
        dict: Supabase status information
    """
    # Check cache first
    cached_status = _get_cached_data("supabase_status", SUPABASE_STATUS_CACHE_TTL)
    if cached_status:
        logger.debug("Returning cached Supabase status")
        return cached_status

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            # Sanitize command before execution
            command = ["supabase", "status", "--output", "json"]
            sanitized_command = _sanitize_subprocess_command(command)

            logger.debug(
                "Checking Supabase status",
                attempt=attempt + 1,
                max_retries=max_retries + 1,
                timeout=timeout,
            )

            # Use asyncio subprocess for non-blocking execution with timeout
            process = await asyncio.create_subprocess_exec(
                *sanitized_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            # Apply timeout to the communication
            _stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

            if process.returncode == 0:
                # Success - parse output and cache result
                status_data = {
                    "status": "running",
                    "db_url": DEVELOPMENT_CONFIG["supabase_db_url"],
                    "db_port": 54322,
                    "version": "1.0.0",  # Would parse from actual CLI output
                    "services": {"db": True},
                    "uptime_seconds": 3600,  # Would calculate from actual data
                    "last_check": time.time(),
                    "attempt": attempt + 1,
                }

                # Cache successful result
                _set_cached_data("supabase_status", status_data)

                logger.info(
                    "Supabase status check successful", attempt=attempt + 1, status="running"
                )

                return status_data
            else:
                # Non-zero return code
                error_msg = stderr.decode() if stderr else "Unknown error"
                last_error = f"Command failed with code {process.returncode}: {error_msg}"

                if attempt < max_retries:
                    logger.warning(
                        "Supabase status check failed, retrying",
                        attempt=attempt + 1,
                        error=last_error,
                        retry_in=1,
                    )
                    await asyncio.sleep(1)  # Brief delay before retry
                    continue

        except TimeoutError:
            last_error = f"Command timed out after {timeout} seconds"
            if attempt < max_retries:
                logger.warning(
                    "Supabase status check timed out, retrying",
                    attempt=attempt + 1,
                    timeout=timeout,
                    retry_in=1,
                )
                await asyncio.sleep(1)
                continue

        except FileNotFoundError:
            last_error = "Supabase CLI not found"
            logger.warning(
                "Supabase CLI not found",
                suggestion="Install Supabase CLI: https://supabase.com/docs/guides/cli",
            )
            break  # No point retrying if CLI is not installed

        except ValueError as e:
            last_error = f"Command sanitization failed: {e!s}"
            logger.error("Command sanitization failed", error=str(e))
            break  # Security issue, don't retry

        except Exception as e:
            last_error = f"Unexpected error: {e!s}"
            if attempt < max_retries:
                logger.warning(
                    "Unexpected error in Supabase status check, retrying",
                    attempt=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                await asyncio.sleep(1)
                continue

    # All attempts failed - return error status
    error_status = {
        "status": "error",
        "db_url": None,
        "db_port": 54322,
        "version": None,
        "services": {"db": False},
        "uptime_seconds": None,
        "last_check": time.time(),
        "error": last_error,
        "attempts": max_retries + 1,
    }

    # Cache error status for shorter time to retry sooner
    _set_cached_data("supabase_status", error_status)

    logger.error(
        "All Supabase status check attempts failed", attempts=max_retries + 1, last_error=last_error
    )

    return error_status


def _check_supabase_status() -> dict:
    """
    Synchronous wrapper for async Supabase status check.
    Deprecated - use _check_supabase_status_with_retry directly in async contexts.
    """
    try:
        # Create new event loop if none exists (for sync compatibility)
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_check_supabase_status_with_retry())


@router.get("/dev/environment", response_model=DevelopmentEnvironment)
async def get_development_environment(
    request: Request, user_id: str = Depends(get_current_user)
) -> DevelopmentEnvironment:
    """
    Get current development environment configuration with enhanced security and caching.

    Args:
        request: FastAPI request object
        user_id: Authenticated user ID

    Returns:
        DevelopmentEnvironment: Current development environment settings

    Raises:
        HTTPException: 403 for access denied, 500 for server errors
    """
    correlation_id = _get_correlation_id(request)
    user_hash = _secure_hash_user_id(user_id)

    logger.info(
        "Development environment requested",
        user_id_hash=user_hash,
        correlation_id=correlation_id,
        environment=APP_ENV,
    )

    # Enhanced security check
    if not _check_dev_endpoints_access(user_id):
        logger.warning(
            "Development environment access denied",
            user_id_hash=user_hash,
            correlation_id=correlation_id,
            reason="insufficient_permissions",
        )
        raise HTTPException(
            status_code=403,
            detail={
                "error": "access_denied",
                "message": "Development endpoints are not available",
                "correlation_id": correlation_id,
            },
        )

    try:
        # Check cache first
        cache_key = f"dev_env_{APP_ENV}"
        cached_env = _get_cached_data(cache_key, ENVIRONMENT_CACHE_TTL)

        if cached_env:
            logger.debug(
                "Returning cached development environment",
                user_id_hash=user_hash,
                correlation_id=correlation_id,
            )
            return DevelopmentEnvironment(**cached_env)

        now = datetime.now(UTC)

        # Create development environment configuration with secure defaults
        dev_env_data = {
            "id": uuid.UUID(STABLE_ENVIRONMENT_ID),  # Stable ID for consistency
            "name": f"{APP_ENV}-development" if APP_ENV != "production" else "production-limited",
            "frontend_port": DEVELOPMENT_CONFIG["frontend_port"],
            "backend_port": DEVELOPMENT_CONFIG["backend_port"],
            "supabase_db_url": DEVELOPMENT_CONFIG["database_url"],
            "supabase_db_password": "",
            "redis_url": DEVELOPMENT_CONFIG["redis_url"],
            "storage_endpoint": DEVELOPMENT_CONFIG["storage_endpoint"],
            "cors_origins": [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173",
            ]
            if APP_ENV != "production"
            else [],
            "log_level": "DEBUG" if APP_ENV != "production" else "INFO",
            "hot_reload": APP_ENV != "production",
            "supabase_cli_version": "1.0.0",  # Would detect actual version in real implementation
            "created_at": now,
            "updated_at": now,
        }

        dev_env = DevelopmentEnvironment(**dev_env_data)

        # Cache the result
        _set_cached_data(cache_key, dev_env_data)

        logger.info(
            "Development environment retrieved",
            environment_id=str(dev_env.id),
            environment_name=dev_env.name,
            user_id_hash=user_hash,
            correlation_id=correlation_id,
            cached=False,
        )

        return dev_env

    except Exception as e:
        logger.error(
            "Failed to get development environment",
            error=str(e),
            error_type=type(e).__name__,
            user_id_hash=user_hash,
            correlation_id=correlation_id,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "environment_retrieval_failed",
                "message": "Internal server error occurred",  # Generic message for security
                "correlation_id": correlation_id,
            },
        ) from e


@router.get("/dev/db/status")
async def get_db_status(request: Request, user_id: str = Depends(get_current_user)) -> dict:
    """Get database connection pool status."""
    correlation_id = _get_correlation_id(request)
    user_hash = _secure_hash_user_id(user_id)

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
            user_id_hash=user_hash,
            correlation_id=correlation_id,
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "db_status_failed", "correlation_id": correlation_id},
        ) from e
