# Docker Cache Troubleshooting

## Problem: Old Frontend Code in Browser

When running the frontend via Docker (`make docker-dev`), you might see old code even after making changes. This happens due to multiple layers of caching.

## Quick Fix

### Option 1: Force Frontend Container Rebuild (Fastest)
```bash
docker compose exec frontend rm -rf node_modules/.vite   # clear Vite cache in the container
docker compose up -d --build --force-recreate frontend
```

This will:
- Clear Vite's dependency cache (it lives in the `frontend_node_modules` volume, not on the host)
- Force Docker to rebuild the frontend image
- Stop and recreate only the frontend container

### Option 2: Full Clean Restart
```bash
make docker-stop   # docker compose down
make docker-dev    # docker compose up --build
```

This will:
- Stop all containers
- Rebuild all images
- Start fresh (named volumes, including `frontend_node_modules`, are kept)

### Option 3: Manual Steps (also clears volumes)
```bash
# Stop containers and delete named volumes (node_modules, Vite cache, Redis/MinIO data)
docker compose down -v

# Rebuild and start
docker compose up --build
```

## Browser Cache

After restarting Docker, also **hard refresh your browser**:

- **Chrome/Firefox (Mac)**: `Cmd + Shift + R`
- **Chrome/Firefox (Windows/Linux)**: `Ctrl + Shift + R`
- **Safari**: `Cmd + Option + R`

Or manually clear cache:
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

## Understanding the Caching Layers

When you run `make docker-dev`, there are multiple caches involved:

### 1. Docker Image Cache
- **What**: Docker caches layers when building images (the `frontend` service builds the `development` stage of `frontend/Dockerfile`, which runs `bun install` and copies the source)
- **When**: On first `docker compose up --build`
- **Fix**: Use `--force-recreate` or `--no-cache`

### 2. Docker Volume Cache
- **What**: Mounted volumes cache file metadata
- **When**: Files are bind-mounted from host to container
- **Fix**: Restart container or use `docker compose down -v`

### 3. Node Modules Cache
- **What**: Named volume `frontend_node_modules` mounted at `/app/node_modules` (the container also runs `bun install` on every start)
- **When**: Dependencies are installed
- **Fix**: Delete volume: `docker compose down -v`

### 4. Vite Build Cache
- **What**: Vite caches pre-bundled dependencies in `node_modules/.vite`. In Docker this is inside the `frontend_node_modules` volume, so deleting `frontend/node_modules/.vite` on the host has no effect on the container
- **When**: During development and building
- **Fix**: `docker compose exec frontend rm -rf node_modules/.vite` (Docker) or `rm -rf frontend/node_modules/.vite` (local dev)

### 5. Browser Cache
- **What**: Browser caches JS/CSS files
- **When**: Files are loaded in browser
- **Fix**: Hard refresh (`Cmd+Shift+R`)

## Development Workflow

### Using Docker (Current Setup)

**Pros:**
- Complete environment isolation
- All services (backend, frontend, Redis, MinIO) in one command
- Production-like setup

**Cons:**
- Slower hot reload
- Multiple caching layers
- Harder to debug

**Best For:**
- Full integration testing
- Testing with all services
- Production-like environment

### Using Local Dev Servers (Alternative)

**Pros:**
- Faster hot reload
- Instant file changes
- Easier debugging
- Better DX (Developer Experience)

**Cons:**
- Need to manage services manually
- Environment differences from production

**Best For:**
- Rapid frontend development
- Quick iterations
- UI/UX work

**How to use:**
```bash
# Start services only (Redis, MinIO, backend)
docker compose up redis minio backend

# In separate terminal, run frontend locally
cd frontend
bun run dev
```

## Docker Compose Volume Strategy

Current setup (`frontend` service in `docker-compose.yml`):

```yaml
volumes:
  - ./frontend/src:/app/src
  - ./frontend/public:/app/public
  - ./frontend/package.json:/app/package.json
  - ./frontend/bun.lock:/app/bun.lock
  - ./frontend/vite.config.ts:/app/vite.config.ts
  - ./frontend/tsconfig.json:/app/tsconfig.json
  - frontend_node_modules:/app/node_modules  # Named volume for node_modules
```

The frontend bind mounts are read-write, so the `bun install` run at container start can update `bun.lock` on the host. (The backend and worker mount `./backend/src` read-only with `:ro`.)

## Troubleshooting Checklist

If you see old code:

- [ ] Clean Vite cache in the container: `docker compose exec frontend rm -rf node_modules/.vite`
- [ ] Stop containers: `docker compose down` (add `-v` to also reset `node_modules`)
- [ ] Rebuild containers: `docker compose up --build`
- [ ] Hard refresh browser: `Cmd+Shift+R` or `Ctrl+Shift+R`
- [ ] Check Docker logs: `docker compose logs -f frontend`
- [ ] Verify files changed: `ls -la frontend/src/components/layout/Navigation.tsx`

## Makefile and Compose Commands

```bash
# Start all containers (docker compose up --build)
make docker-dev

# Quick container rebuild (frontend only)
docker compose up -d --build --force-recreate frontend

# Stop all containers (docker compose down)
make docker-stop

# View logs
docker compose logs -f frontend
docker compose logs -f backend
```

## Verifying Changes Applied

### Check if file exists in container:
```bash
docker compose exec frontend ls -la /app/src/components/layout/Navigation.tsx
```

### Force complete rebuild (nuclear option):
```bash
docker compose down -v  # Delete all volumes
docker compose build --no-cache  # Ignore all caches
docker compose up
```

## Best Practices

1. **For frontend development**: Use local `bun run dev` for faster iteration
2. **For integration testing**: Use Docker to test complete system
3. **Before commits**: Test with Docker to ensure production-like behavior
4. **After pulling changes**: Run `make docker-stop && make docker-dev` to get a clean state (`docker compose down -v` if dependencies changed)

## Hot Module Reload (HMR) in Docker

Vite's HMR should work in Docker, but it can be flaky. If HMR isn't working:

1. **Check Vite is running**:
   ```bash
   docker compose logs frontend | grep "ready in"
   ```

2. **Verify WebSocket connection**:
   - Open browser DevTools → Network tab
   - Look for WebSocket connection to `ws://localhost:3000`
   - Should show "101 Switching Protocols"

3. **Force HMR trigger**:
   - Make a small change to any source file
   - Save the file
   - Watch Docker logs: `docker compose logs -f frontend`

## Related Issues

- If you see "Connection refused" → Backend not started yet
- If you see "Module not found" → Run `docker compose down -v` to clear node_modules
- If changes not applying → Hard refresh browser + restart container
