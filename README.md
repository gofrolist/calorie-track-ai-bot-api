# Calories Count — Photo‑First POC

Frontend: Vercel (Telegram Mini App) • Backend: FastAPI on Fly.io • Redis: Upstash • DB: Supabase • Object Storage: Tigris • Vision: OpenAI gpt‑5‑mini

## Features
- Presigned PUT to Tigris (S3‑compatible) for meal photos
- Queue job to Upstash Redis; background worker processes photos
- Vision estimate via OpenAI gpt‑5‑mini → deterministic kcal aggregation with min/max
- Persist users/photos/estimates/meals in Supabase Postgres

## Quick start

### Development Setup
```bash
# Install dependencies
uv sync

# Edit .env file with your actual service credentials
nano .env

# Start development server
uv run uvicorn src.calorie_track_ai_bot.main:app --reload --host 0.0.0.0 --port 8000

# Health check
curl http://localhost:8000/health/live
```

### Docker Setup
```bash
cp .env.example .env
# fill values
docker compose up --build

# In another terminal (optional) create tables in Supabase:
psql "$SUPABASE_DATABASE_URL" -f infra/schema.sql
```

### Testing
```bash
# Run basic tests (no external services required)
uv run pytest tests/services/test_config.py tests/api/v1/test_health.py tests/api/v1/test_auth.py -v

# Run all tests (requires .env with real credentials)
uv run pytest tests/ -v

# Run linting
uv run ruff check

# Run type checking
uv run pyright
```

## Endpoints
- `POST /api/v1/photos` → presign URL
- `POST /api/v1/photos/{photo_id}/estimate` → enqueue estimation
- `GET /api/v1/estimates/{id}` → fetch estimate
- `POST /api/v1/meals` → create from estimate or manual kcal

OpenAPI JSON: `GET /openapi.json`.

## Environment Configuration

### Local Development
Create a `.env` file in the project root with your service credentials:

```bash
# Application
APP_ENV=dev

# OpenAI
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-5-mini

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Redis
REDIS_URL=redis://localhost:6379

# Tigris/S3 (using standard AWS S3 environment variables)
AWS_ENDPOINT_URL_S3=https://fly.storage.tigris.dev
AWS_ACCESS_KEY_ID=tid_xxxxxx
AWS_SECRET_ACCESS_KEY=tsec_xxxxxx
BUCKET_NAME=your-bucket-name
AWS_REGION=auto
```

### GitHub Actions
For CI/CD, configure GitHub secrets in your repository settings. See [docs/GITHUB_SECRETS.md](docs/GITHUB_SECRETS.md) for detailed instructions.

## Available Commands

```bash
# Development
uv sync                    # Install dependencies
uv run uvicorn src.calorie_track_ai_bot.main:app --reload  # Start dev server
uv run pytest tests/ -v   # Run all tests
uv run ruff check         # Run linting
uv run pyright           # Run type checking

# Docker
docker compose up --build  # Build and run with Docker
docker compose down        # Stop Docker containers

# Deployment
flyctl deploy            # Deploy to Fly.io (requires flyctl)
```
