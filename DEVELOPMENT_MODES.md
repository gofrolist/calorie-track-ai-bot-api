# Development Modes Comparison

## Quick Reference

| Mode | Command | Services | Redis | Supabase | Storage | Use Case |
|------|---------|----------|-------|----------|---------|----------|
| **Docker Full Stack** | `make docker-dev` | All containerized | Local (6379) | Supabase CLI | MinIO | Full integration testing |
| **Local Dev** | `make dev` | Local processes | Upstash (cloud) | Cloud/CLI | Tigris/Cloud | Rapid development |
| **Backend Only** | `cd backend && make run` | Backend only | From .env | From .env | From .env | Backend testing |

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
- Hardcoded in `docker-compose.yml`
- Ignores `backend/.env` for service URLs
- Always uses local containers

**Pros:**
- ✅ Complete environment in one command
- ✅ Production-like setup
- ✅ Isolated from host system
- ✅ Easy to reset (`make docker-restart`)
- ✅ No production credentials needed
- ✅ Free to run (no cloud costs)

**Cons:**
- ❌ Slower iteration (Docker overhead)
- ❌ Caching issues (fixed with `make docker-restart`)
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
✅ Frontend (local)       → localhost:5173
⚠️  Redis (Upstash)       → Cloud service
⚠️  Supabase (cloud)      → Cloud database
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
✅ Frontend (local)       → cd frontend && npm run dev
```

**Commands:**
```bash
# Start backend services in Docker
docker compose up redis minio backend

# In separate terminal, run frontend locally
cd frontend
npm run dev
```

**Pros:**
- ✅ **Best of both worlds**
- ✅ Fast frontend hot reload
- ✅ Backend in Docker (isolated)
- ✅ No production credentials needed
- ✅ No cloud costs

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
  SUPABASE_URL: http://host.docker.internal:54321
  AWS_ENDPOINT_URL_S3: http://minio:9000

  # These CAN come from .env:
  OPENAI_API_KEY: ${OPENAI_API_KEY:-}      # ← Optional from shell
  TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:-}
```

### Local Mode (.env used for everything)

```bash
# backend/.env
REDIS_URL=rediss://your-redis.upstash.io:6379  # ← Used in local mode
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_DB_PASSWORD=your-password
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
npm run dev
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
make docker-restart  # Clean restart
# Then hard refresh browser (Cmd+Shift+R)
```

### Issue: "Connection refused" to backend

**Problem:** Backend not started or Supabase not running

**Solution:**
```bash
# 1. Start Supabase CLI (required for Docker mode)
supabase start

# 2. Then start Docker
make docker-dev
```

## Quick Start Guide

### For New Developers

1. **Clone repo**
2. **Copy template:** `cp backend/env.template backend/.env`
3. **Start Supabase:** `supabase start`
4. **Start Docker:** `make docker-dev`
5. **Open browser:** http://localhost:3000

You're done! No credentials needed.

### For Existing Developers

If you already have `backend/.env` with production credentials:

```bash
# Docker will IGNORE these values for Redis/Supabase/MinIO
# It uses local containers instead
make docker-dev

# Everything just works!
```

## File Structure

```
calorie-track-ai-bot-api/
├── docker-compose.yml          ← SINGLE docker-compose file
├── Makefile                    ← Docker commands (docker-dev, docker-restart, etc.)
├── backend/
│   ├── .env                    ← Production credentials (gitignored)
│   ├── env.template            ← Template for .env
│   └── Makefile                ← Backend commands (run, test, etc.)
└── frontend/
    └── Makefile                ← Frontend commands (if any)
```

## Key Takeaways

1. ✅ **One docker-compose.yml** in root (backend/docker-compose.yml deleted)
2. ✅ **Docker mode uses local containers** (ignores production URLs in .env)
3. ✅ **Local mode uses production services** (reads from .env)
4. ✅ **Hybrid mode recommended for frontend dev** (best performance)
5. ✅ **No credentials needed for Docker development**
