# CLAUDE.md

Telegram Mini App for AI-powered food photo analysis and calorie tracking. Monorepo:

- **`backend/`** — Python 3.12, FastAPI, Neon PostgreSQL, deployed on Fly.io
- **`frontend/`** — React 19, TypeScript 5.9, Vite 7, deployed on Vercel

See `backend/CLAUDE.md` and `frontend/CLAUDE.md` for detailed commands, architecture, and code style.

## Root Commands

```bash
make dev              # Start both backend (port 8000) and frontend (port 3000)
make test             # Run all tests (backend + frontend)
make lint             # Lint both
make docker-dev       # Full stack via Docker Compose
```

## CI/CD

GitHub Actions workflows trigger on path-based changes:
- `backend-ci.yml` → `backend-build.yml` → `backend-deploy.yml` (Fly.io)
- `frontend-ci.yml` → `frontend-deploy.yml` (Vercel)

## Database

Neon PostgreSQL. Schema in `backend/infra/schema.sql`. Set `DATABASE_URL` env var.
