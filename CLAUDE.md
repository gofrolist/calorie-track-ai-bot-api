# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Telegram Mini App for AI-powered food photo analysis and calorie tracking. Monorepo with two main directories:

- **`backend/`** — Python 3.12, FastAPI, Neon PostgreSQL (psycopg3), Upstash Redis, Tigris S3, OpenAI vision API
- **`frontend/`** — React 19, TypeScript 5.9, Vite 7, Telegram Mini App SDK

Deployed: frontend on Vercel, backend on Fly.io.

## Common Commands

### Root-level (orchestrates both)
```bash
make dev              # Start both backend (port 8000) and frontend (port 3000)
make test             # Run all tests (backend + frontend)
make lint             # Lint both
make docker-dev       # Full stack via Docker Compose
```

### Backend (`cd backend`)
```bash
make dev              # FastAPI with hot reload (port 8000)
make worker           # Start background estimate worker
make test             # All pytest tests
make test-unit        # Unit tests only (excludes tests/integration/)
make test-integration # Integration tests only
uv run pytest tests/path/to/test_file.py -v          # Single test file
uv run pytest tests/path/to/test_file.py::test_name  # Single test function
make lint             # ruff check
make typecheck        # pyright
make check            # lint + typecheck
make format           # ruff format
make coverage         # pytest with coverage report
```

### Frontend (`cd frontend`)
```bash
npm run dev           # Vite dev server (port 3000)
npm run build         # TypeScript compile + Vite build
npm test              # Vitest via test-ci.js
npx vitest run tests/path/to/file.test.ts             # Single test file
npm run test:e2e      # Playwright E2E tests
npm run lint          # ESLint (max 10 warnings)
npm run check         # type-check + lint + format:check
npm run format        # Prettier
npm run i18n:validate # Check EN/RU translation key consistency
```

### Database (Neon PostgreSQL)
Database is hosted on Neon. Set `DATABASE_URL` env var to the pooled connection string.
Schema is in `backend/infra/schema.sql`.

## Architecture

### Backend

**Entry point:** `backend/src/calorie_track_ai_bot/main.py` — FastAPI app with middleware stack (CORS, structured logging, correlation ID tracking).

**API routes** are under `/api/v1/` with routers in individual files: `meals.py`, `photos.py`, `estimates.py`, `goals.py`, `statistics.py`, `feedback.py`, `bot.py` (Telegram webhook handler), etc.

**Key services:**
- `database.py` — Async connection pool (`psycopg_pool.AsyncConnectionPool`) lifecycle
- `db.py` — All database operations via raw SQL, user ID resolution with 5-min cache
- `estimator.py` — OpenAI vision API for calorie estimation
- `queue.py` — Redis job queue for async photo processing
- `storage.py` — Tigris S3 presigned URL generation
- `telegram.py` — Telegram bot client

**Worker:** `workers/estimate_worker.py` — Background processor that dequeues photo estimation jobs.

**Schemas:** `schemas.py` — Pydantic v2 models auto-generated from OpenAPI spec (`make codegen`).

**Database schema:** `backend/infra/schema.sql` — Tables: `users`, `photos`, `estimates`, `meals`, `goals`.

**Auth pattern:** Telegram user ID passed via `x-user-id` header. Correlation ID middleware adds `x-correlation-id` to all requests/responses.

**Error handling:** `@handle_api_errors(context_name)` decorator on route handlers.

### Frontend

**Entry:** `src/main.tsx` → `src/app.tsx` (React Router with lazy-loaded pages).

**Pages:** `Meals`, `Stats`, `Goals`, `Feedback` — in `src/pages/`.

**Key components:** `ThemeDetector`, `LanguageDetector`, `SafeAreaWrapper` handle Telegram environment integration (theme, locale, device safe areas).

**Services:** `src/services/api.ts` — Axios instance with request interceptors that attach `X-Correlation-ID` (UUID per session), `x-user-id` (Telegram user ID), and `Authorization: Bearer` token if session exists.

**i18n:** EN and RU translations in `src/i18n/`. Validate key parity with `npm run i18n:validate`.

**Path alias:** `@/*` maps to `src/*` in imports.

### CI/CD

GitHub Actions workflows trigger on path-based changes:
- `backend-ci.yml` → `backend-build.yml` → `backend-deploy.yml` (Fly.io)
- `frontend-ci.yml` → `frontend-deploy.yml` (Vercel)
- Database schema managed via `backend/infra/schema.sql` (applied to Neon)

## Code Style

### Backend
- **Formatter/linter:** Ruff (line length 100, double quotes, LF endings)
- **Type checking:** Pyright basic mode
- **Ruff rules:** E, F, I, B, UP, RUF (E501 ignored)
- **Package manager:** `uv` (not pip)

### Frontend
- **TypeScript:** Strict mode
- **Linter:** ESLint with React Hooks plugin, max 10 warnings
- **Formatter:** Prettier
- **Unused vars:** Prefix with `_` to suppress warnings
- **Testing:** Vitest for unit tests, Playwright for E2E (mobile-first: iPhone 14 Pro, Samsung Galaxy S23, iPad Pro)
