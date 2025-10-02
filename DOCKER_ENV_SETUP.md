# Docker Environment Setup

## Important: Single Docker Compose File

This project uses **ONE docker-compose.yml** file located at the root directory. The old `backend/docker-compose.yml` has been removed to avoid confusion.

## Two Different Development Modes

You can run the application in two different ways, each with different environment configurations:

### 1. Docker Development (`make docker-dev` from root)

**Uses**: Local containerized services
- ✅ Redis: `redis://redis:6379/0` (local container)
- ✅ Supabase: `http://host.docker.internal:54321` (Supabase CLI)
- ✅ MinIO: `http://minio:9000` (local S3-compatible storage)

**Environment**: Defined in `docker-compose.yml`
**Config Location**: Root `docker-compose.yml` (lines 53-83, 115-132)

### 2. Local Development (`make dev` from root)

**Uses**: Production/cloud services (requires credentials)
- ⚠️ Redis: Upstash Redis (production URL from `backend/.env`)
- ⚠️ Supabase: Production/staging URL from `backend/.env`
- ⚠️ Storage: Tigris/production S3 from `backend/.env`

**Environment**: Defined in `backend/.env`
**Config Location**: `backend/.env` (not in git, use `backend/env.template`)

## Why Only One docker-compose.yml?

Previously, there were two docker-compose files which caused confusion:
- ❌ `docker-compose.yml` (root) - Full stack with frontend
- ❌ `backend/docker-compose.yml` - Backend only, simpler

**This created problems:**
- Running `make docker-dev` from root used one file
- Running `docker compose up` from backend directory used another
- Different Redis configurations caused connection errors
- Hard to maintain consistency

**Now:**
- ✅ Only `docker-compose.yml` in root directory
- ✅ All Docker commands use the same configuration
- ✅ Consistent behavior regardless of where you run commands
- ✅ Explicitly sets `REDIS_URL=redis://redis:6379/0` to override any `.env` values

## The Problem You Encountered (Now Fixed)

**Symptom:** Worker error: `"Error -5 connecting to fly-buddy-gym-bot-redis.upstash.io:6379"`

**Root Cause:**
- Your `backend/.env` has `REDIS_URL` pointing to production Upstash
- The old `backend/docker-compose.yml` loaded this via `env_file: [.env]`
- Worker tried to connect to Upstash instead of local Redis container

**Solution:**
- Removed `backend/docker-compose.yml` entirely
- Root `docker-compose.yml` explicitly sets `REDIS_URL=redis://redis:6379/0`
- This **overrides** any value from `backend/.env`
- Worker now connects to local Redis container

## Solution

### ✅ **Root docker-compose.yml is Now Fixed**

The `docker-compose.yml` in the root directory now **explicitly sets** all environment variables in the `environment:` section, which takes precedence over any `.env` file values.

Key changes:
```yaml
backend:
  environment:
    # Redis - ALWAYS use local container
    REDIS_URL: redis://redis:6379/0
    # ... other Docker-specific values
```

### ✅ **For Root Directory Docker Development**

When running from root:
```bash
make docker-dev
```

**Environment variables are:**
- ✅ Hardcoded in `docker-compose.yml`
- ✅ Always use local containers
- ✅ Safe from `.env` conflicts

### ⚠️ **For Backend Directory Docker**

When running from `backend/`:
```bash
cd backend
docker compose up
```

**Environment variables come from:**
- `backend/.env` file
- `backend/docker-compose.yml`

This is meant for backend-only testing.

## Recommended Workflows

### Frontend Development (Fastest)
```bash
# Start backend services in Docker
docker compose up redis minio backend

# Run frontend locally
cd frontend
npm run dev
```

**Pros:**
- Instant hot reload
- No Docker caching issues
- Fast iteration

### Full Stack Development
```bash
# From root directory
make docker-dev
```

**Pros:**
- Complete environment
- Production-like setup
- All services containerized

**Cons:**
- Slower rebuild times
- Caching issues (fixed with `make docker-restart`)

### Backend Testing Only
```bash
cd backend
make run  # Uses backend/.env with production services
```

**Pros:**
- Quick backend iteration
- Uses real production services (Upstash, Supabase)

**Cons:**
- Requires production credentials
- Costs money (Upstash, Tigris)

## Environment Variable Precedence

In Docker Compose, environment variables are loaded in this order (later overrides earlier):

1. **Environment variables in shell** (e.g., `export REDIS_URL=...`)
2. **`.env` file** (if `env_file:` is specified)
3. **`environment:` section** in docker-compose.yml ← **HIGHEST PRIORITY**

We rely on #3 to ensure Docker always uses local services.

## Troubleshooting

### "Name has no usable address" (Upstash)

**Symptom**: Worker tries to connect to Upstash instead of local Redis

**Cause**: Backend `.env` has `REDIS_URL` pointing to Upstash

**Fix**: Environment variables in `docker-compose.yml` should override this, but if not:
```bash
# Verify environment in container
docker compose exec backend env | grep REDIS_URL
# Should show: REDIS_URL=redis://redis:6379/0

# If it shows Upstash URL, the environment section isn't working
# Make sure you're using root docker-compose.yml:
docker compose -f docker-compose.yml up
```

### Frontend Showing Old Code

**Symptom**: Changes not visible in browser

**Fix**:
```bash
make docker-restart  # Clean restart
# Then hard refresh browser (Cmd+Shift+R)
```

### MinIO Connection Issues

**Symptom**: "Failed to connect to S3"

**Fix**: Ensure MinIO is running:
```bash
docker compose ps
# Should show minio as "healthy"

# If not healthy, check logs:
docker compose logs minio
```

## Quick Reference

| Command | Use Case | Speed |
|---------|----------|-------|
| `make docker-dev` | Start all services | Normal |
| `make docker-restart` | Clean restart (fixes cache) | Slow |
| `make docker-rebuild-frontend` | Rebuild frontend only | Fast |
| `make docker-stop` | Stop all containers | Fast |
| `docker compose down -v` | Nuclear option (delete volumes) | Slow |

## Production Deployment

For production, use the values from `backend/.env` which should point to:
- ✅ Upstash Redis (production)
- ✅ Supabase (production project)
- ✅ Tigris S3 (production bucket)

The docker-compose.yml is **only for local development**.
