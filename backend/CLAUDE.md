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
make codegen          # Regenerate schemas.py from specs/openapi.yaml

# Single test
uv run pytest tests/path/to/test_file.py -v
uv run pytest tests/path/to/test_file.py::test_name
```

## Source Layout

```
src/calorie_track_ai_bot/
├── main.py              # FastAPI app, middleware stack, router registration
├── schemas.py           # AUTO-GENERATED from specs/openapi.yaml (do not edit manually)
├── api/v1/              # Route handlers (one file per resource)
├── services/            # Business logic and external integrations
│   ├── config.py        # All env var loading, feature flags
│   ├── db.py            # Supabase client (`sb`), user ID resolution with 5-min cache
│   ├── estimator.py     # OpenAI vision API for calorie estimation
│   ├── queue.py         # Redis job queue (`r` client)
│   ├── storage.py       # Tigris S3 presigned URLs
│   └── telegram.py      # Telegram bot client
├── utils/
│   └── error_handling.py  # @handle_api_errors decorator, auth helpers
└── workers/
    └── estimate_worker.py  # Background photo estimation processor
```

## Key Patterns

**Auth:** No JWT/session auth. Telegram user ID arrives via `x-user-id` header. Use `validate_user_authentication(request)` from `utils/error_handling.py` to extract it. The `db.py` service resolves telegram_id to internal UUID user with a 5-minute cache.

**Error handling:** Route handlers use `@handle_api_errors("context_name")` decorator. It re-raises `HTTPException` as-is and wraps unexpected exceptions into 500s with logging.

**Schemas:** `schemas.py` is auto-generated — run `make codegen` after modifying `specs/openapi.yaml`. Do not edit `schemas.py` manually.

**Middleware order** (in `main.py`): request logging → correlation ID → CORS. The correlation ID middleware binds `x-correlation-id` to structlog context vars.

**Testing:** All external services (Supabase, Redis, OpenAI, S3, Telegram) are mocked at module level in `tests/conftest.py` via `unittest.mock.patch`. Test env vars are set in `pytest.ini`. Use fixtures like `api_client`, `mock_supabase_client`, `mock_redis_client`, `mock_openai_client` from conftest.

**Database:** Schema defined in `infra/schema.sql`. Tables: `users`, `photos`, `estimates`, `meals`, `goals`. All PKs are UUID via `gen_random_uuid()`. Users are keyed by `telegram_id` (bigint, unique).

## Code Style

- **Package manager:** `uv` (not pip) — use `uv run` to execute commands
- **Ruff:** line length 100, double quotes, LF, rules E/F/I/B/UP/RUF (E501 ignored)
- **Pyright:** basic mode, excludes tests directory
- **Python:** 3.12, Pydantic v2, async FastAPI handlers
