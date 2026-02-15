# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See also the root-level `../CLAUDE.md` for monorepo-wide commands and full architecture overview.

## Commands (run from `backend/`)

```bash
make dev              # FastAPI with hot reload on port 8000
make worker           # Background estimate worker
make test             # All tests (pytest)
make test-unit        # Unit tests only (ignores tests/integration/)
make test-integration # Integration tests only
make check            # lint (ruff) + typecheck (pyright)
make format           # ruff format
make openapi-export   # Export OpenAPI spec JSON from FastAPI app

# Single test
uv run pytest tests/path/to/test_file.py -v
uv run pytest tests/path/to/test_file.py::test_name
```

## Source Layout

```
src/calorie_track_ai_bot/
├── main.py              # FastAPI app, middleware stack, router registration
├── schemas.py           # Pydantic models (edit directly, source of truth for API schema)
├── api/v1/              # Route handlers (one file per resource)
├── services/            # Business logic and external integrations
│   ├── config.py        # All env var loading, feature flags
│   ├── database.py      # Async connection pool (psycopg_pool) lifecycle
│   ├── db/              # Database operations (per-domain modules)
│   │   ├── _base.py     # resolve_user_id with 5-min TTL cache (max 1000 entries)
│   │   ├── users.py, photos.py, estimates.py, meals.py, goals.py
│   │   ├── summaries.py, ui_config.py, inline_analytics.py
│   │   └── __init__.py  # Re-exports all public functions
│   ├── estimator.py     # OpenAI vision API for calorie estimation
│   ├── queue.py         # Redis job queue (`r` client)
│   ├── storage.py       # Tigris S3 presigned URLs
│   └── telegram.py      # Telegram bot client
├── utils/
│   └── error_handling.py  # @handle_api_errors decorator
└── workers/
    └── estimate_worker.py  # Background photo estimation processor
```

## Key Patterns

**Auth:** No JWT/session auth. Telegram user ID arrives via `x-user-id` header. Use `Depends(get_telegram_user_id)` or `Depends(get_authenticated_user_id)` from `api/v1/deps.py`. The `db/_base.py` module resolves telegram_id to internal UUID user with a 5-minute TTL cache (max 1000 entries).

**Error handling:** Route handlers use `@handle_api_errors("context_name")` decorator. It re-raises `HTTPException` as-is and wraps unexpected exceptions into generic 500s (no internal details leaked).

**Schemas:** `schemas.py` is the source of truth for API request/response models. Edit it directly. FastAPI auto-generates the OpenAPI spec from these models at runtime (`/docs`, `/openapi.json`). Use `make openapi-export` to dump the spec to a file.

**Middleware order** (in `main.py`): request logging → correlation ID → CORS. The correlation ID middleware binds `x-correlation-id` to structlog context vars.

**Testing:** All external services (Database, Redis, OpenAI, S3, Telegram) are mocked at module level in `tests/conftest.py` via `unittest.mock.patch`. Test env vars are set in `pytest.ini`. Use fixtures like `api_client`, `mock_db_pool`, `mock_redis_client`, `mock_openai_client` from conftest. The `mock_db_pool` fixture patches `get_pool()` and returns `(mock_pool, mock_conn)` — pool uses `Mock()` (synchronous `pool.connection()`), connection uses `AsyncMock()`.

**Database:** Schema defined in `infra/schema.sql`. Tables: `users`, `photos`, `estimates`, `meals`, `goals`. All PKs are UUID via `gen_random_uuid()`. Users are keyed by `telegram_id` (bigint, unique).

## Deployment

Do NOT offer to deploy to Fly.io unless explicitly asked. GitHub CI deploys automatically on push to main.

## Code Style

- **Package manager:** `uv` (not pip) — use `uv run` to execute commands
- **Ruff:** line length 100, double quotes, LF, rules E/F/I/B/UP/RUF (E501 ignored)
- **Pyright:** basic mode, excludes tests directory
- **Python:** 3.12, Pydantic v2, async FastAPI handlers
- **Before committing:** run `uv run ruff format .` to auto-format all changed files. Pre-commit hooks enforce formatting and will reject unformatted code.
