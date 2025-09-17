# Frontend - Telegram Mini App

This folder contains the Telegram Mini App for the Calorie Track AI Bot.

## Setup from Community Template

Based on [Telegram-Mini-Apps community templates](https://github.com/telegram-mini-apps):

### Recommended Templates
- `reactjs-template` - React + TypeScript + Vite + @telegram-apps/sdk
- `nextjs-template` - Next.js + TypeScript + TON Connect + tma.js

### Quick Start
```bash
# Option 1: React template
npx degit telegram-mini-apps/reactjs-template frontend/
cd frontend/
npm install

# Option 2: Next.js template
npx degit telegram-mini-apps/nextjs-template frontend/
cd frontend/
npm install
```

### Key Features to Implement
- Today view: meal list + daily totals
- Meal detail: edit calories/macros
- Week/Month stats: charts and trends
- Goals: daily calorie targets
- Share functionality (no export needed)
- Internationalization: English + Russian

### Development
```bash
npm run dev     # Start dev server
npm run build   # Build for production
npm run deploy  # Deploy to Vercel
```

## Architecture

- **Auth**: Telegram WebApp initData validation
- **API Client**: Generated from OpenAPI spec (`backend/specs/openapi.yaml`)
- **Routing**: Mini App navigation patterns
- **UI**: Mobile-first, responsive design
- **State**: Local state + API sync

## Deployment

- Host on Vercel or equivalent
- No secrets in client code
- Cache-control for static assets
