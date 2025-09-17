# Research (Phase 0) — Frontend Mini App

## Decisions
- Mini App templates: Use community templates from [Telegram-Mini-Apps](https://github.com/telegram-mini-apps) for baseline structure, theming, and SDK usage.
- Backend contracts: Drive endpoints strictly from `backend/specs/openapi.yaml`.
- Toolkit: React + TypeScript + Vite (`reactjs-template`) or Next.js (`nextjs-template`) with `tma.js`/`@telegram-apps/sdk`.
- I18n: English and Russian at launch (spec FR-017).
- Sharing: Provide a share option in Mini App; no data export at this stage (spec FR-016).

## Rationale
- Templates accelerate delivery and align with Telegram Mini App UX norms.
- Contract-first avoids frontend/backend drift and simplifies testing.
- React/Next ecosystem provides strong tooling, i18n, and deployment support on Vercel.

## Alternatives Considered
- Native Telegram SDK vs community `@telegram-apps/sdk`: community templates are richer and updated frequently.
- Next.js vs React + Vite: Next offers SSR/ISR but Mini App primarily client-side; either template acceptable.

## Open Questions (resolved)
- Languages at launch → EN + RU.
- Export vs share → Share only.

## References
- Templates and SDKs: [Telegram-Mini-Apps organization](https://github.com/telegram-mini-apps)
