# Calorie Track AI Bot

[![Backend CI](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-ci.yml)
[![Backend Build](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-build.yml/badge.svg)](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-build.yml)

A full-stack application for tracking calories using AI-powered photo analysis with multi-photo support and enhanced meal history features.

## Features

### Multi-Photo Meal Tracking
- Upload up to 5 photos per meal for better calorie estimation
- AI-powered analysis using OpenAI GPT-4 Vision
- Automatic macronutrient breakdown (protein, carbs, fats)
- Telegram bot integration with media group support

### Enhanced Meal History
- Calendar-based meal navigation
- Inline meal card expansion
- Instagram-style photo carousel
- Meal editing and deletion with confirmation
- Responsive design for mobile devices

### Technical Features
- FastAPI backend with automatic OpenAPI documentation
- React frontend with TypeScript
- Supabase PostgreSQL database
- Tigris S3-compatible storage
- Upstash Redis for background job queuing

## Repository Structure

This repository is organized into backend and frontend components:

- `backend/` - FastAPI application with Telegram bot functionality
- `frontend/` - React-based Telegram Mini App with meal tracking interface

## Quick Start

### Backend Development

See [backend/README.md](backend/README.md) for detailed backend setup instructions.

```bash
# Install dependencies
cd backend && uv sync

# Start development server
cd backend && uv run uvicorn src.calorie_track_ai_bot.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

See [frontend/README.md](frontend/README.md) for detailed frontend setup instructions.

```bash
# Install dependencies
cd frontend && npm install

# Start development server
cd frontend && npm run dev
```

## Features

### Multi-Photo Meal Tracking
- Upload up to 5 photos per meal
- AI-powered calorie and macronutrient estimation
- Instagram-style photo carousel
- Thumbnail optimization for fast loading

### Enhanced Meal History
- Calendar-based meal browsing
- Date range filtering
- Meal editing and deletion
- Responsive design for mobile devices

### Telegram Integration
- Telegram Bot for photo submission
- Telegram Mini App for meal management
- Media group support for multi-photo uploads
- Real-time AI estimation processing

## Available Commands

```bash
# Backend development (run from backend folder)
cd backend
make venv               # Install dependencies
make run                # Start dev server
make test               # Run all tests
make precommit          # Run linting and formatting
make validate           # Validate OpenAPI spec
make codegen            # Generate schemas from OpenAPI spec

# Or run commands directly with uv
cd backend
uv sync --all-extras    # Install dependencies
uv run uvicorn calorie_track_ai_bot.main:app --reload  # Start dev server
uv run pytest           # Run all tests
uv run ruff check       # Run linting
uv run pyright          # Run type checking

# Deployment (requires flyctl)
cd backend
flyctl deploy           # Deploy to Fly.io
```

## Architecture

- **Backend**: FastAPI on Fly.io
- **Database**: Supabase Postgres
- **Queue**: Redis (Upstash)
- **Storage**: Tigris (S3-compatible)
- **AI**: OpenAI GPT-5-mini for image analysis
- **Frontend**: Telegram Mini App (planned)

## CI/CD Workflows

This repository uses optimized GitHub Actions workflows that only run when relevant files change:

### Workflow Strategy

- **`backend-ci.yml`** - Backend CI (tests, linting, type checking)
  - Triggers: Backend changes, workflow changes
  - Skips: Frontend-only changes

- **`backend-build.yml`** - Docker image build and push
  - Triggers: Backend changes, workflow changes
  - Skips: Frontend-only changes

- **`backend-deploy.yml`** - Deploy to Fly.io
  - Triggers: After successful build or on version tags
  - Only runs when backend is actually built

- **`frontend-ci.yml`** - Frontend CI (when implemented)
  - Triggers: Frontend changes only
  - Placeholder for future frontend development

### Benefits

✅ **Efficient**: No unnecessary backend builds for frontend changes
✅ **Fast**: Parallel execution of backend and frontend CI when both change
✅ **Cost-effective**: Reduced GitHub Actions minutes usage
✅ **Simple**: Clear, focused workflows without duplication
✅ **Scalable**: Easy to add more workflows as the project grows

## Documentation

- [Backend Documentation](backend/README.md)
- [GitHub Secrets Setup](docs/GITHUB_SECRETS.md)
