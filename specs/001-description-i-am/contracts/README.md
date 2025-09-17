# Contracts Overview (Phase 1)

Source of truth: `backend/specs/openapi.yaml`

## Endpoint Mapping to Requirements
- FR-001 (analyze photo, reply with calories/macros)
  - Bot webhook: `POST /bot` (receives photo message; backend orchestrates presign + enqueue)
  - Photo upload init: `POST /api/v1/photos`
  - Enqueue estimate: `POST /api/v1/photos/{photo_id}/estimate`
  - Fetch estimate: `GET /api/v1/estimates/{estimate_id}`
- FR-003/FR-004/FR-005 (logs, corrections, deletions in Mini App)
  - Create meal: `POST /api/v1/meals` (manual or from estimate with overrides)
- Health & Ops
  - `GET /health/live`, `GET /health/ready`, `GET /healthz`
- Telegram Bot management
  - `POST /bot/setup`, `GET /bot/webhook-info`, `DELETE /bot/webhook`
- Mini App auth (Telegram WebApp)
  - `POST /auth/telegram/init`

Note: Listing meals, updating meals, or statistics endpoints may be designed in subsequent iterations and added to the spec accordingly.
