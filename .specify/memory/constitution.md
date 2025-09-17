## Calorie Track AI Bot — Constitution

### Core Principles

- **Telegram-first UX**: The primary user experience is a Telegram Bot with a Mini App. All flows must be optimized for chat-first interactions, short latencies, and clear, friendly messaging. Mini App complements, not replaces, chat.
- **API-first, contract-driven**: `backend/specs/openapi.yaml` is the single source of truth for client/server contracts. Any change to endpoints or schemas requires an OpenAPI update, version bump, and codegen/test updates before implementation.
- **Test-first and CI gates (non-negotiable)**: New behavior must be covered by tests. A change cannot merge unless unit/integration tests pass and static checks are green: `uv run ruff check`, `uv run pyright`, `uv run pytest`.
- **Privacy & security by default**: Minimize PII, use row-level security in Postgres, never commit secrets, prefer ephemeral tokens, and ensure explicit user consent for data processing. Logs must not leak secrets or raw images.
- **Simplicity & reliability**: Prefer simple, observable designs. Make operations idempotent and safe to retry. Apply backpressure and timeouts to external calls. Degrade gracefully and communicate errors clearly to the user.
- **Observability built-in**: Structured logs with correlation IDs, request/response sampling for non-sensitive metadata, and clear operational dashboards for webhook rate, queue depth, and worker latency.

### Architecture & Technology Requirements

- **Backend (Python/FastAPI)**
  - Framework: FastAPI with async endpoints, served by uvicorn.
  - API: Implement and maintain endpoints defined in `backend/specs/openapi.yaml`, including `/api/v1/photos`, `/api/v1/photos/{photo_id}/estimate`, `/api/v1/estimates/{id}`, `/api/v1/meals`, and Telegram bot endpoints (`/bot`, `/bot/setup`, `/bot/webhook-info`, `/bot/webhook`).
  - Auth: Telegram WebApp init data verification for Mini App sessions; bot chat identity for webhook flows.
  - AI/Vision: Use OpenAI Vision with model `gpt-5-mini` for image analysis; keep prompts/versioning in code and test determinism where feasible.
  - Storage: Use Tigris (S3-compatible) with presigned URLs for photo uploads; never proxy raw image bytes through the API.
  - Queue/Worker: Upstash Redis queue enqueues estimation jobs; a background worker performs vision analysis and persists estimates.
  - Database: Supabase Postgres; enable RLS and policies; migrations via Alembic.

- **Worker**
  - Dedicated process/module consuming the Redis queue.
  - Idempotent job processing keyed by `estimate_id` and `photo_id`.
  - Retries with jitter; poison-queue handling for repeated failures; metrics for attempts/latency.

- **Frontend (Telegram Mini App)**
  - Platform: Telegram WebApp embedded in Telegram; responsive mobile-first UI.
  - Template: Start from the Mini App template (routing, theming, telemetry, API client) and only extend necessary features.
  - Auth: Use Telegram `initData` validation flow to obtain a short-lived session; store tokens in memory (not persistent storage) and refresh as needed.
  - API client: Generated or hand-written client strictly following `openapi.yaml`. All requests include correlation IDs and respect server backoff headers.
  - UX flows: Quick upload → queue → status polling; manual kcal entry; meal confirmation from estimate with overrides.
  - Hosting: Vercel or equivalent static hosting with cache-control tuned for static assets; no secrets embedded in client code.

- **Configuration & Secrets**
  - Local dev uses `.env`; CI/production use platform secrets; never commit secrets.
  - No secrets in `fly.toml`; use Fly.io secrets for runtime configuration.
  - Prefer `SUPABASE_URL` and `SUPABASE_DB_PASSWORD` (or service role key) over a raw `DATABASE_URL` string where applicable; enforce RLS in production.
  - Required env (prod): `SUPABASE_URL`, service role key, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `REDIS_URL`, `AWS_ENDPOINT_URL_S3`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BUCKET_NAME`.
  - Optional env: `LOG_LEVEL`, `APP_ENV`, `WEBHOOK_URL`, `AWS_REGION`.

### Non-Functional Requirements

- **Performance**: P95 API latency ≤ 300 ms for lightweight endpoints; estimation enqueue ≤ 500 ms; background estimation end-to-end P95 ≤ 8 s (network/AI bound).
- **Throughput & rate limits**: Support at least 10 RPS sustained on webhook and presign endpoints; enforce per-user and global rate limits to protect upstreams.
- **Resilience**: Timeouts on external calls (S3/OpenAI/Redis) with retries and circuit breakers; idempotent handlers; webhook verification to avoid replay.
- **Cost controls**: Track OpenAI token/image usage; apply size limits to uploads; reject unsupported MIME types early.
- **Security**: HSTS/HTTPS only; validate Telegram signatures; sanitize user inputs; pin dependencies via `uv` lock; regular dependency scans.
- **Observability**: Structured logs, request IDs, queue depth gauge, worker processing histograms; health probes `/health/live` and `/health/ready` must remain fast and dependency-light.

### Development Workflow & Quality Gates

- **Branching & reviews**: Feature branches with small, reviewable PRs. All PRs require review and must reference OpenAPI changes when contracts are modified.
- **Static checks & tests**: Before merge, run:
  - `uv run ruff check` (no warnings on changed files)
  - `uv run pyright` (no errors)
  - `uv run pytest` (green, including new tests for new files/classes/functions)
- **Migrations**: Alembic migration for any persisted schema change; apply in CI to verify; ensure RLS compatible policies are updated.
- **Codegen**: If using client/server codegen from OpenAPI, regenerate artifacts and commit them when the spec changes.
- **Versioning**: Semantic versioning for the API and the Mini App. Breaking API changes require a major version bump and a deprecation window.
- **Makefile & scripts**: Operational commands live in the `Makefile` (dev, test, deploy) to ensure reproducibility.
- **GitHub Actions**: CI runs lint, type-check, tests, and (optionally) OpenAPI validation. Keep action versions stable; only update with intent.

### Telegram Bot Requirements

- **Webhook**: `/bot` must be reachable publicly with correct TLS; `/bot/setup` automates webhook registration in production; `/bot/webhook-info` and `/bot/webhook` support inspection and teardown.
- **Commands**: At minimum `/start`, help/usage hints, and graceful handling of unknown messages. Photo/document messages trigger presign + enqueue flow with user feedback and links to Mini App for review.
- **Internationalization**: Default English with a path to localized strings; auto-detect via Telegram `language_code` where safe.
- **Abuse & error handling**: Rate-limit abusive chats; redact sensitive content in logs; provide actionable error messages to users.

### Data & Compliance

- **Data retention**: Define retention windows for raw photos and derived estimates; allow user-initiated deletion of photos/estimates.
- **Access control**: Enforce that users only see and mutate their own data; service role key is restricted to the backend service.
- **Backups**: Rely on Supabase managed backups; document restore procedures and test periodically.

## Governance

- This constitution supersedes ad-hoc practices. Any deviation requires a documented rationale and a follow-up amendment.
- Amendments require: (1) proposal PR updating this document, (2) review/approval, (3) migration plan where applicable, and (4) updated tests and runbooks.
- All PRs must state compliance with this constitution or note which clauses are amended.

**Version**: 1.0.0 | **Ratified**: 2025-09-17 | **Last Amended**: 2025-09-17
