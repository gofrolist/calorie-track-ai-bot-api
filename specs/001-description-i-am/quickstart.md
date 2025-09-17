# Quickstart (Phase 1)

## Prerequisites
- Python 3.12
- `uv` for dependency management
- `.env` with required variables (see backend README)
- Telegram bot token from @BotFather

## Backend (Dev)
```bash
make venv
# Fill .env with service credentials
make run
# Health check
curl http://localhost:8000/health/live
```

## Telegram Webhook
```bash
# Configure webhook (in dev, use tunnel or set a public URL)
curl -X POST http://localhost:8000/bot/setup
# Inspect webhook info
curl http://localhost:8000/bot/webhook-info
```

## Frontend (Mini App)

### Setup from Template
```bash
# Choose one:
# Option 1: React template
npx degit telegram-mini-apps/reactjs-template frontend/
cd frontend/
npm install

# Option 2: Next.js template
npx degit telegram-mini-apps/nextjs-template frontend/
cd frontend/
npm install
```

### Development
```bash
cd frontend/
npm run dev     # Start dev server
npm run build   # Build for production
```

### Features to Implement
- Today view: meal list + daily totals
- Meal detail: edit calories/macros
- Week/Month stats: charts and trends
- Goals: daily calorie targets
- Share functionality
- Internationalization: English + Russian

### Deploy
- Host on Vercel: `npm run deploy`
- Ensure no secrets in client code

## Try It
1. In Telegram, send `/start` to your bot.
2. Send a food photo; you should receive calories/macros shortly.
3. Open the Mini App from bot to review, correct, and view stats.
```
