# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

React 19 + TypeScript 5.9 + Vite 7 frontend for a Telegram Mini App that does AI-powered food photo analysis and calorie tracking. Deployed on Vercel. The backend is a separate FastAPI service in `../backend/`.

## Commands

```bash
npm run dev                # Vite dev server on port 3000
npm run build              # tsc -b && vite build
npm run check              # type-check + lint + format:check (run before committing)
npm run lint               # ESLint (max 10 warnings allowed)
npm run format             # Prettier
npm run i18n:validate      # Verify EN/RU translation key parity

# Testing
npm test                                              # All unit tests (vitest via test-ci.js)
npx vitest run src/path/to/file.test.ts               # Single test file
npx vitest run src/path/to/file.test.ts -t "test name" # Single test
npm run test:e2e                                       # Playwright E2E tests
npm run test:e2e:headed                                # E2E with browser visible
```

## Architecture

### Entry & Routing

`src/main.tsx` initializes the Telegram WebApp SDK (`expand()`, `ready()`, sets header/bg colors), imports i18n, then mounts the React app.

`src/app.tsx` is the core component: sets up React Router with 4 lazy-loaded pages (`/` → Meals, `/stats`, `/goals`, `/feedback`), provides `TelegramWebAppContext` (user, theme, language, safe areas), and wraps everything in `ErrorBoundary` + `SafeAreaWrapper`.

### Telegram Integration

The app runs inside Telegram's WebApp container. Three detector components in `src/components/` handle environment sensing:

- **ThemeDetector** — resolves theme from Telegram SDK, system `prefers-color-scheme`, or manual override. Sets CSS custom properties (`--tg-bg-color`, `--tg-text-color`, etc.) and `data-theme` attribute on `<html>`.
- **LanguageDetector** — resolves language (en/ru) from Telegram user data, browser locale, or stored preference. Priority: Telegram > browser > stored > default.
- **SafeAreaWrapper** — handles device notches/home indicators via CSS `env(safe-area-inset-*)` and `visualViewport` API.

User ID is extracted from `window.Telegram?.WebApp?.initDataUnsafe?.user?.id` with fallbacks to URL params and localStorage.

### API Layer

`src/services/api.ts` — single Axios instance with request interceptors that attach:
- `X-Correlation-ID` (UUID per session for distributed tracing)
- `x-user-id` (Telegram user ID)
- `Authorization: Bearer` token if session exists

API functions are organized by domain: `photosApi`, `mealsApi`, `goalsApi`, `dailySummaryApi`, `estimatesApi`, `analyticsApi`, etc. Backend returns snake_case; the API layer transforms to camelCase.

`apiUtils` provides composite operations: `initializeApplication()` (parallel config/theme/language fetch), `uploadPhotoAndEstimate()` (full photo flow), `pollEstimate()` (30 attempts, 2s interval).

### Config

`src/config.ts` — centralized config from `import.meta.env`. Access via `config.apiBaseUrl`, `config.features.*`, etc. Helper functions: `configUtils.isInTelegram()`, `configUtils.isFeatureEnabled()`, `configUtils.getUserLanguage()`.

### i18n

`src/i18n/index.ts` — i18next with nested keys (e.g., `today.title`, `meals.list.empty`). EN and RU only. All user-facing text must use `t('key')` from `useTranslation()`. Run `npm run i18n:validate` after adding/changing keys.

### Pages & Hooks Pattern

Pages use a consistent pattern:
```tsx
const { t } = useTranslation();
const telegramContext = useContext(TelegramWebAppContext);
const { data, loading, error, refetch } = useCustomHook();
```

Custom hooks (e.g., `src/hooks/useMealsPage.ts`) fetch data with `Promise.allSettled()`, return `{ data, loading, error, refetch, mutationMethods }`, and implement optimistic updates that revert on failure.

## Key Conventions

- **Path alias:** `@/*` maps to `src/*` in imports
- **Unused variables:** prefix with `_` to suppress ESLint warnings
- **Lazy loading:** all pages use `React.lazy()` + `Suspense`
- **CSS theming:** all colors reference Telegram CSS variables (`--tg-*`), never hardcoded
- **Vite code splitting:** manual chunks for react-vendor, swiper-vendor, i18n-vendor (configured in `vite.config.ts`)
- **E2E tests:** mobile-first — Playwright configured with iPhone 14 Pro, Samsung Galaxy S23, iPad Pro, Desktop Chrome viewports
- **Test mocks:** `src/test-setup.ts` mocks localStorage, matchMedia, ResizeObserver, IntersectionObserver, and Telegram WebApp with sample user data
