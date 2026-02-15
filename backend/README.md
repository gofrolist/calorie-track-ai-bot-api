# Calories Count — Photo‑First POC

Frontend: Vercel (Telegram Mini App) • Backend: FastAPI on Fly.io • Redis: Upstash • DB: Neon PostgreSQL • Object Storage: Tigris • Vision: OpenAI gpt‑5‑mini

## Repository Structure

This repository is organized into backend and frontend components:

- `backend/` - FastAPI application with Telegram bot functionality
- `frontend/` - Frontend application (to be added)

## Features
- Presigned PUT to Tigris (S3‑compatible) for meal photos
- Queue job to Upstash Redis; background worker processes photos
- Vision estimate via OpenAI gpt‑5‑mini → deterministic kcal aggregation with min/max
- Persist users/photos/estimates/meals in Neon PostgreSQL Postgres

## Quick start

### Development Setup
```bash
# Install dependencies
make venv

# Edit .env file with your actual service credentials
nano .env

# Start development server
make run

# Health check
curl http://localhost:8000/health/live
```

### Docker Setup
```bash
cp .env.example .env
# fill values
docker compose up --build

# In another terminal (optional) create tables in Neon PostgreSQL:
psql "$DATABASE_URL" -f infra/schema.sql
```

### Testing
```bash
# Run basic tests (no external services required)
uv run pytest tests/services/test_config.py tests/api/v1/test_health.py tests/api/v1/test_auth.py -v

# Run all tests (requires .env with real credentials)
make test

# Run linting
uv run ruff check

# Run type checking
uv run pyright
```

## Endpoints

### API Endpoints
- `POST /api/v1/photos` → presign URL
- `POST /api/v1/photos/{photo_id}/estimate` → enqueue estimation
- `GET /api/v1/estimates/{id}` → fetch estimate
- `POST /api/v1/meals` → create from estimate or manual kcal

### Statistics Endpoints (✨ NEW)
- `GET /api/v1/statistics/daily` → Daily nutrition aggregates (last 7/30/90 days)
- `GET /api/v1/statistics/macros` → Macronutrient breakdown by percentage

### Feedback Endpoints (✨ NEW)
- `POST /api/v1/feedback` → Submit user feedback (bug reports, feature requests)
- `GET /api/v1/feedback/{id}` → Retrieve feedback submission (admin only)

### Telegram Bot Endpoints
- `POST /bot` → Telegram webhook handler (receives messages from Telegram)
- `POST /bot/setup` → Setup Telegram webhook
- `GET /bot/webhook-info` → Get current webhook information
- `DELETE /bot/webhook` → Delete current webhook

OpenAPI JSON: `GET /openapi.json`.
Complete API documentation: `specs/openapi.yaml`

### New Features in v2.0
- **Interactive Statistics**: Real-time data aggregation with date range filtering
- **User Feedback System**: In-app feedback collection with admin Telegram notifications
- **Enhanced Localization**: 180+ translation keys fully synchronized (EN/RU)

## Logging and Debugging

The application includes comprehensive logging to help debug issues. Logging is controlled by environment variables:

### Log Levels
- `LOG_LEVEL`: Set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL` (default: `INFO`)

### Enabling Debug Logging
To enable debug logging for troubleshooting:

```bash
# In your .env file
LOG_LEVEL=DEBUG
```

### Log Output
Logs include:
- **INFO**: General application flow, API requests, database operations
- **DEBUG**: Detailed information about internal operations, data processing
- **ERROR**: Error conditions with full stack traces
- **WARNING**: Non-critical issues that should be noted

### Telegram Bot Debugging
When debugging Telegram bot issues:
1. Check that the webhook URL is correctly configured in `fly.toml`
2. Ensure the `/bot` endpoint is accessible
3. Monitor logs for incoming webhook requests
4. Verify database connections and external service availability
5. Use `/bot/setup` endpoint to configure webhook with Telegram
6. Check `/bot/webhook-info` to verify webhook status

### Environment Variables

The application requires the following environment variables:

#### Required for Production
- `DATABASE_URL`: Neon PostgreSQL connection string
- `OPENAI_API_KEY`: OpenAI API key for image analysis
- `TELEGRAM_BOT_TOKEN`: Telegram bot token from @BotFather
- `REDIS_URL`: Redis connection URL for job queue
- `AWS_ENDPOINT_URL_S3`: Tigris S3 endpoint URL
- `AWS_ACCESS_KEY_ID`: Tigris access key
- `AWS_SECRET_ACCESS_KEY`: Tigris secret key
- `BUCKET_NAME`: Tigris bucket name

#### Optional
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `APP_ENV`: Application environment (dev, prod)
- `WEBHOOK_URL`: Telegram webhook URL (auto-configured in production)
- `ADMIN_NOTIFICATION_CHAT_ID`: Telegram chat ID for admin feedback notifications
- `FEEDBACK_NOTIFICATIONS_ENABLED`: Enable/disable feedback Telegram notifications (true/false)

### Common Issues
- **Silent bot responses**: Check webhook URL configuration and endpoint accessibility
- **Photo processing failures**: Verify Tigris/S3 configuration and OpenAI API key
- **Database errors**: Check Neon PostgreSQL connection and table schema
- **Bot not responding**: Verify `TELEGRAM_BOT_TOKEN` is set correctly
- **Webhook issues**: Use `/bot/webhook-info` to check webhook status

## Environment Configuration

### Local Development
Create a `.env` file in this folder with your service credentials:

```bash
# Application
APP_ENV=dev

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-5-mini

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# Redis
REDIS_URL=redis://localhost:6379

# Tigris/S3 (using standard AWS S3 environment variables)
AWS_ENDPOINT_URL_S3=https://fly.storage.tigris.dev
AWS_ACCESS_KEY_ID=tid_xxxxxx
AWS_SECRET_ACCESS_KEY=tsec_xxxxxx

# Logging Configuration
LOG_LEVEL=INFO

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
WEBHOOK_URL=https://your-app.fly.dev/bot
USE_WEBHOOK=true
BUCKET_NAME=your-bucket-name
AWS_REGION=auto
```

## Telegram Bot Setup

### 1. Create a Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Save the bot token you receive

### 2. Configure Environment Variables
Add your bot token to your `.env` file:
```bash
TELEGRAM_BOT_TOKEN=your-bot-token-here
WEBHOOK_URL=https://your-app.fly.dev/bot
USE_WEBHOOK=true
```

### 3. Deploy and Test
The webhook is automatically configured when your app starts up! Just deploy and test:

```bash
# Deploy your app (webhook will be set automatically)
flyctl deploy

# Test your bot by sending /start command
```

### 4. Test Your Bot
1. Find your bot on Telegram (search for the username you created)
2. Send `/start` command
3. Send a photo of food to test calorie estimation

### 5. Manual Webhook Management (Optional)
If you need to manually manage the webhook:
```bash
# Check webhook status
curl https://your-app.fly.dev/bot/webhook-info

# Manually setup webhook (usually not needed)
curl -X POST https://your-app.fly.dev/bot/setup

# Delete webhook
curl -X DELETE https://your-app.fly.dev/bot/webhook
```

### GitHub Actions
For CI/CD, configure GitHub secrets in your repository settings. See [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md) for detailed instructions.

## Available Commands

```bash
# Development (using Makefile)
make venv                # Install dependencies
make run                 # Start dev server
make test                # Run all tests
make precommit           # Run linting and formatting
make validate            # Validate OpenAPI spec
make codegen             # Generate schemas from OpenAPI spec

# Development (using uv directly)
uv sync --all-extras     # Install dependencies
uv run uvicorn calorie_track_ai_bot.main:app --reload  # Start dev server
uv run pytest            # Run all tests
uv run ruff check        # Run linting
uv run pyright          # Run type checking

# Docker
docker compose up --build  # Build and run with Docker
docker compose down        # Stop Docker containers

# Deployment
flyctl deploy            # Deploy to Fly.io (requires flyctl)
```
