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
- Initialize from community templates: see [Telegram-Mini-Apps](https://github.com/telegram-mini-apps)
  - Recommended: `reactjs-template` or `nextjs-template`
- Implement views for: Today (list + totals), Meal detail (edit), Week/Month stats, Goals
- Ensure mobile-first responsive design; support English and Russian

## Try It
1. In Telegram, send `/start` to your bot.
2. Send a food photo; you should receive calories/macros shortly.
3. Open the Mini App from bot to review, correct, and view stats.
```
