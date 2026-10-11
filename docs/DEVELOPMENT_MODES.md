# Development Modes Comparison

## Quick Reference

| Mode | Command | Services | Redis | Database | Storage | Use Case |
|------|---------|----------|-------|----------|---------|----------|
| **Docker Full Stack** | `make docker-dev` | All containerized | Local (6379) | Neon (`DATABASE_URL` from shell or root `.env`) | MinIO | Full integration testing |
| **Local Dev** | `make dev` | Local processes | From `backend/.env` (Upstash or local) | Neon (cloud) | Tigris/Cloud | Rapid development |
| **Backend Only** | `cd backend && make dev` | Backend only | From .env | From .env | From .env | Backend testing |

## Detailed Comparison

### 1. Docker Full Stack (`make docker-dev`)

**Run From:** Root directory

**What Starts:**
```
✅ Redis (container)      → localhost:6379
✅ MinIO (container)      → localhost:9000 (API), localhost:9001 (Console)
✅ Backend (container)    → localhost:8000
✅ Worker (container)     → Background process
✅ Frontend (container)   → localhost:3000
```

**Environment Configuration:**
- Hardcoded in `docker-compose.yml` (`environment:` of the `backend` and `worker` services)
- `DATABASE_URL` is substituted from your shell or a root-level `.env` file; if unset it falls back to `postgresql://postgres:postgres@host.docker.internal:5432/calorie_track`
- `backend/.env` is not used for service URLs (it is copied into the image and loaded by python-dotenv, which never overrides variables already set by Compose)
- Redis and storage always use local containers

**Pros:**
- ✅ Complete environment in one command
- ✅ Production-like setup
- ✅ Isolated from host system
- ✅ Easy to reset (`make docker-stop && make docker-dev`)
- ✅ Only `DATABASE_URL` is required (OpenAI/Telegram keys optional)
- ✅ No Redis/storage cloud costs

**Cons:**
- ❌ Slower iteration (Docker overhead)
- ❌ Caching issues (see [DOCKER_CACHE_TROUBLESHOOTING.md](DOCKER_CACHE_TROUBLESHOOTING.md))
- ❌ More memory usage
- ❌ Frontend hot reload can be flaky

**Best For:**
- Full system integration testing
- Testing all services together
- QA testing
- New developers (simple setup)

### 2. Local Development (`make dev`)

**Run From:** Root directory

**What Starts:**
```
✅ Backend (local)        → localhost:8000
✅ Frontend (local)       → localhost:3000
❌ Worker                 → not started (set ENABLE_WORKER=true or run `make -C backend worker`)
⚠️  Redis (Upstash)       → Cloud service
⚠️  Neon (cloud)           → Cloud database
⚠️  Tigris (cloud)        → Cloud storage
```

**Environment Configuration:**
- Uses `backend/.env` file
- Connects to production/staging services
- Requires credentials

**Pros:**
- ✅ Fast hot reload
- ✅ Instant file changes
- ✅ Better debugging
- ✅ Uses real production services
- ✅ Lower memory usage

**Cons:**
- ❌ Requires production credentials (OPENAI_API_KEY, TELEGRAM_BOT_TOKEN, etc.)
- ❌ Costs money (Upstash, Tigris)
- ❌ Can accidentally modify production data
- ❌ Requires internet connection

**Best For:**
- Rapid frontend development
- Quick backend iterations
- Testing with real AI (OpenAI)
- Debugging specific issues

### 3. Hybrid Mode (Recommended for Frontend Dev)

**Run From:** Root directory

**What Starts:**
```
✅ Redis (container)      → docker compose up redis
✅ MinIO (container)      → docker compose up minio
✅ Backend (container)    → docker compose up backend
✅ Frontend (local)       → cd frontend && bun run dev
```

**Commands:**
```bash
# Start backend services in Docker (add `worker` if you need photo estimation)
docker compose up redis minio backend

# In separate terminal, run frontend locally
cd frontend
bun run dev
```

**Pros:**
- ✅ **Best of both worlds**
- ✅ Fast frontend hot reload
- ✅ Backend in Docker (isolated)
- ✅ Only `DATABASE_URL` needed
- ✅ No Redis/storage cloud costs

**Cons:**
- ❌ Need to manage two terminals
- ❌ Slightly more complex

**Best For:**
- ⭐ **Frontend development** (most common)
- UI/UX iteration
- Component development
- Styling work

## Environment Variables Explained

### Docker Mode (.env NOT used for service URLs)

```yaml
# docker-compose.yml (root)
environment:
  REDIS_URL: redis://redis:6379/0          # ← Hardcoded
  DATABASE_URL: ${DATABASE_URL:-postgresql://postgres:postgres@host.docker.internal:5432/calorie_track}
  AWS_ENDPOINT_URL_S3: http://minio:9000

  # These come from your shell or a root-level .env (not backend/.env):
  OPENAI_API_KEY: ${OPENAI_API_KEY:-}      # ← Optional from shell
  TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}
```

### Local Mode (.env used for everything)

```bash
# backend/.env
REDIS_URL=rediss://your-redis.upstash.io:6379  # ← Used in local mode
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
AWS_ENDPOINT_URL_S3=https://fly.storage.tigris.dev
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456:ABC...
```

## How to Switch Modes

### Start Docker Mode
```bash
make docker-dev
# or
docker compose up
```

### Stop Docker, Start Local
```bash
make docker-stop
make dev
```

### Hybrid (Frontend Local)
```bash
# Terminal 1: Start backend services
docker compose up redis minio backend

# Terminal 2: Run frontend
cd frontend
bun run dev
```

## Troubleshooting

### Issue: "Error connecting to Upstash" in Docker

**Problem:** Docker trying to use production Redis from `.env`

**Solution:** ✅ Already fixed! Root `docker-compose.yml` now hardcodes `REDIS_URL=redis://redis:6379/0`

**Verify:**
```bash
docker compose exec backend env | grep REDIS_URL
# Should output: REDIS_URL=redis://redis:6379/0
```

### Issue: Frontend showing old code in Docker

**Solution:**
```bash
make docker-stop && make docker-dev  # Clean restart (rebuilds images)
# Then hard refresh browser (Cmd+Shift+R)
```

### Issue: "Connection refused" to backend

**Problem:** Backend not started or database not reachable

**Solution:**
```bash
# Ensure DATABASE_URL is exported in your shell (or set in a root-level .env), then start Docker
export DATABASE_URL='postgresql://user:pass@ep-xxx.neon.tech/neondb?sslmode=require'
make docker-dev
```

## Quick Start Guide

### For New Developers

1. **Clone repo**
2. **Copy template:** `cp backend/env.template backend/.env` (supplies non-service settings)
3. **Export DATABASE_URL** with your Neon connection string (shell or root-level `.env`; Compose does not read `backend/.env`)
4. **Start Docker:** `make docker-dev`
5. **Open browser:** http://localhost:3000

You're done! Only the database URL is required; OpenAI and Telegram keys are optional.

### For Existing Developers

If you already have `backend/.env` with production credentials:

```bash
# Docker will IGNORE these values for Redis/Database/MinIO
# Redis and storage use local containers; DATABASE_URL comes from your shell/root .env
make docker-dev

# Everything just works!
```

## File Structure

```
calorie-track-ai-bot-api/
├── docker-compose.yml          ← SINGLE docker-compose file
├── Makefile                    ← Root commands (dev, test, docker-dev, docker-stop, etc.)
├── backend/
│   ├── .env                    ← Production credentials (gitignored)
│   ├── env.template            ← Template for .env
│   └── Makefile                ← Backend commands (dev, worker, test, etc.)
└── frontend/
    └── Makefile                ← Frontend commands (dev, test, check, etc.)
```

## Key Takeaways

1. ✅ **One docker-compose.yml** in root (backend/docker-compose.yml deleted)
2. ✅ **Docker mode uses local containers** (ignores production URLs in .env)
3. ✅ **Local mode uses production services** (reads from .env)
4. ✅ **Hybrid mode recommended for frontend dev** (best performance)
5. ✅ **Docker development only needs `DATABASE_URL`** (exported in the shell or a root-level `.env`)
