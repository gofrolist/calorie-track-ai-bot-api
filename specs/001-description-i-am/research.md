# Research (Phase 0)

## Decisions
- Mini App templates: Use community templates from [Telegram-Mini-Apps](https://github.com/telegram-mini-apps) for baseline structure, theming, and SDK usage.
- Backend contracts: Drive endpoints strictly from `backend/specs/openapi.yaml`.
- Vision model: OpenAI Vision `gpt-5-mini` for calorie/macros estimation.
- Storage: Tigris S3-compatible with presigned uploads; never proxy raw images through backend.
- Queue: Upstash Redis for estimation jobs; idempotent workers with retries and DLQ strategy.
- DB: Supabase Postgres with RLS; Alembic for migrations.
- I18n: English and Russian at launch (spec FR-017).
- Sharing: Provide a share option in Mini App; no data export at this stage (spec FR-016).

## Rationale
- Templates accelerate delivery and align with Telegram Mini App UX norms.
- Contract-first avoids frontend/backend drift and simplifies testing.
- Presigned uploads reduce bandwidth/cost and improve reliability.
- Managed queue/DB reduce ops burden, with clear scaling paths.

## Alternatives Considered
- Native Telegram SDK vs community `@telegram-apps/sdk`: community templates are richer and updated frequently.
- Direct uploads via backend: rejected due to cost/latency and complexity.
- Local inference: rejected for MVP due to cost/latency/ops trade-offs.

## Open Questions (resolved)
- Languages at launch → EN + RU.
- Export vs share → Share only.

## References
- Templates and SDKs: [Telegram-Mini-Apps organization](https://github.com/telegram-mini-apps)
