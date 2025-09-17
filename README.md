# Calorie Track AI Bot

[![Backend CI](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-ci.yml)
[![Backend Build](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-build.yml/badge.svg)](https://github.com/evgenii.vasilenko/calorie-track-ai-bot-api/actions/workflows/backend-build.yml)

A full-stack application for tracking calories using AI-powered photo analysis.

## Repository Structure

This repository is organized into backend and frontend components:

- `backend/` - FastAPI application with Telegram bot functionality
- `frontend/` - Frontend application (to be added)

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

Frontend components will be added to the `frontend/` folder in future iterations.

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
