# Contracts Overview (Phase 1) — Frontend API Usage

Source of truth: `backend/specs/openapi.yaml`. The Mini App consumes these endpoints via a typed client.

## Endpoint Mapping to Requirements
- FR-001 (analyze photo, reply with calories/macros)
  - Bot webhook: `POST /bot` (receives photo message; backend orchestrates presign + enqueue)
  - Photo upload init: `POST /api/v1/photos`
  - Enqueue estimate: `POST /api/v1/photos/{photo_id}/estimate`
  - Fetch estimate: `GET /api/v1/estimates/{estimate_id}`
- FR-003/FR-004/FR-005 (logs, corrections in Mini App)
  - Create meal: `POST /api/v1/meals` (manual or from estimate with overrides)
  - [Future] List meals, update/delete meals endpoints will be added in backend spec.
- Health & Ops
  - `GET /health/live`, `GET /health/ready`, `GET /healthz`
- Telegram Bot management
  - `POST /bot/setup`, `GET /bot/webhook-info`, `DELETE /bot/webhook`
- Mini App auth (Telegram WebApp)
  - `POST /auth/telegram/init`

Client considerations:
- Include Telegram initData → session token from `/auth/telegram/init` when calling APIs
- Add correlation ID header for observability
- Handle 4xx/5xx gracefully and surface actionable messages in UI
