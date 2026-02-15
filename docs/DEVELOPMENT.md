# Development Setup Guide

This guide will help you set up and run the Calorie Track AI Bot application locally for development and testing.

## Prerequisites

Make sure you have the following installed:
- **Node.js** (v18 or later) - [Download](https://nodejs.org/)
- **Python 3.12** - [Download](https://python.org/)
- **uv** (Python package manager) - [Install](https://docs.astral.sh/uv/getting-started/installation/)
- **npm** (comes with Node.js)

## Quick Start

### 1. Clone and Setup
```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd calorie-track-ai-bot-api

# Complete setup (installs all dependencies)
make setup
```

### 2. Configure Environment

#### Backend Configuration
Create a `.env` file in the `backend/` directory with your service credentials:

```bash
# Copy the example (if available)
cp backend/.env.example backend/.env

# Or create manually
nano backend/.env
```

Required environment variables for backend:
```env
# Application
APP_ENV=dev
LOG_LEVEL=INFO

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-5-mini

# Database (Neon PostgreSQL)
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# Redis
REDIS_URL=redis://localhost:6379

# Tigris/S3
AWS_ENDPOINT_URL_S3=https://fly.storage.tigris.dev
AWS_ACCESS_KEY_ID=tid_xxxxxx
AWS_SECRET_ACCESS_KEY=tsec_xxxxxx
BUCKET_NAME=your-bucket-name

# Telegram
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
USE_WEBHOOK=false
WEBHOOK_URL=https://your-public-url/bot

# Inline Mode
INLINE_MODE_ENABLED=false
INLINE_HASH_SALT=change-me-inline-hash-salt
INLINE_THROUGHPUT_PER_MIN=60
INLINE_BURST_RPS=5

# Optional API overrides
API_BASE_URL=http://localhost:8000
```

> Inline mode prerequisites: when enabling inline features, set `INLINE_MODE_ENABLED=true`, provide a high-entropy `INLINE_HASH_SALT`, and keep `INLINE_THROUGHPUT_PER_MIN` / `INLINE_BURST_RPS` aligned with the 60 requests-per-minute (≈5 rps burst) capacity. See `specs/004-add-inline-mode/quickstart.md` for end-to-end inline verification steps.

#### Frontend Configuration
Create a `.env.local` file in the `frontend/` directory:

```bash
cd frontend
nano .env.local
```

Frontend environment variables:
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Development Features
VITE_ENABLE_DEBUG_LOGGING=true
VITE_ENABLE_ERROR_REPORTING=false
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEV_TOOLS=true

# App Metadata
VITE_APP_VERSION=1.0.0

# API Timeout (milliseconds)
VITE_API_TIMEOUT=30000
```

### 3. Start Development Servers

```bash
# Start both backend and frontend
make dev
```

This will start:
- **Backend API**: http://localhost:8000
- **Frontend App**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs

## Development Commands

### Essential Commands
```bash
make setup          # Complete setup (backend + frontend)
make dev            # Start both servers in development mode
make test           # Run all tests
make lint           # Run linting for both backend and frontend
make clean          # Clean up temporary files
make help           # Show all available commands
```

### Backend Commands
```bash
make dev-backend    # Start only backend server
make test-backend   # Run backend tests
make lint-backend   # Run backend linting and type checking
```

### Frontend Commands
```bash
make dev-frontend   # Start only frontend server
make test-frontend  # Run frontend tests
make build-frontend # Build frontend for production
```

### Utility Commands
```bash
make health-check   # Check if backend is running
make telegram-setup # Setup Telegram webhook
make api-docs       # Open API documentation
make check-deps     # Verify all dependencies are installed
```

## Testing

### Backend Testing
```bash
# Run all backend tests
make test-backend

# Run specific test categories
cd backend
uv run pytest tests/services/ -v
uv run pytest tests/api/v1/ -v
```

### Frontend Testing
```bash
# Run frontend unit tests
make test-frontend

# Run end-to-end tests
make test-e2e
```

## Telegram Bot Setup

### 1. Create a Telegram Bot
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` command
3. Follow the prompts to create your bot
4. Save the bot token you receive

### 2. Configure Webhook (Development)
```bash
# Start your backend first
make dev-backend

# In another terminal, setup the webhook
make telegram-setup
```

### 3. Test Your Bot
1. Find your bot on Telegram
2. Send `/start` command
3. Send a photo of food to test calorie estimation

## API Testing

### Using the API Documentation
1. Start the backend: `make dev-backend`
2. Open http://localhost:8000/docs
3. Use the interactive Swagger UI to test endpoints

### Using curl
```bash
# Health check
curl http://localhost:8000/health/live

# Get webhook info
curl http://localhost:8000/bot/webhook-info

# Test photo upload (example)
curl -X POST http://localhost:8000/api/v1/photos \
  -H "Content-Type: application/json" \
  -d '{"content_type": "image/jpeg"}'
```

## Frontend Development

### Running the Frontend
```bash
# Start frontend development server
make dev-frontend

# Or navigate to frontend directory
cd frontend
npm run dev
```

### Frontend Features
- **Today View**: Daily meal tracking and progress
- **Meal Detail**: Edit and manage individual meals
- **Stats**: Weekly and monthly progress charts
- **Goals**: Set and track daily calorie goals
- **Telegram Integration**: Full WebApp SDK integration

### Frontend Architecture
- **React 18** with TypeScript
- **Vite** for fast development
- **React Router** for navigation
- **i18next** for internationalization (EN/RU)
- **Telegram WebApp SDK** for bot integration
- **Axios** for API communication

## Troubleshooting

### Common Issues

#### Backend Issues
```bash
# Check if backend is running
make health-check

# Check logs
make logs

# Restart backend
make restart
```

#### Frontend Issues
```bash
# Clear frontend cache
make clean-frontend

# Reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### Environment Issues
```bash
# Verify dependencies
make check-deps

# Check environment files exist
ls -la backend/.env
ls -la frontend/.env.local
```

### Port Conflicts
If you have port conflicts:
- **Backend**: Change port in `backend/Makefile` (line with `--port 8000`)
- **Frontend**: Change port in `frontend/vite.config.ts`

### Database Issues
- Ensure your Neon PostgreSQL project is active
- Check that DATABASE_URL is set correctly
- Verify the database schema is up to date (see `backend/infra/schema.sql`)

## Production Deployment

### Backend (Fly.io)
```bash
cd backend
flyctl deploy
```

### Frontend (Vercel)
```bash
cd frontend
vercel deploy
```

## Contributing

1. Make your changes
2. Run tests: `make test`
3. Run linting: `make lint`
4. Commit your changes
5. Create a pull request

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the backend README.md
3. Check the API documentation at http://localhost:8000/docs
4. Create an issue in the repository
