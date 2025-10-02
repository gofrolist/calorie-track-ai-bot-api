# Docker Cache Troubleshooting

## Problem: Old Frontend Code in Browser

When running the frontend via Docker (`make docker-dev`), you might see old code even after making changes. This happens due to multiple layers of caching.

## Quick Fix

### Option 1: Force Frontend Container Rebuild (Fastest)
```bash
make docker-rebuild-frontend
```

This will:
- Stop and recreate only the frontend container
- Force Docker to rebuild the frontend image
- Clear Vite's cache

### Option 2: Full Clean Restart
```bash
make docker-restart
```

This will:
- Stop all containers
- Clean frontend dist and Vite cache
- Rebuild all containers
- Start fresh

### Option 3: Manual Steps
```bash
# Stop containers
docker compose down

# Remove frontend cache
rm -rf frontend/dist frontend/node_modules/.vite

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
- **What**: Docker caches layers when building images
- **When**: On first `docker compose up --build`
- **Fix**: Use `--force-recreate` or `--no-cache`

### 2. Docker Volume Cache
- **What**: Mounted volumes cache file metadata
- **When**: Files are bind-mounted from host to container
- **Fix**: Restart container or use `docker compose down -v`

### 3. Node Modules Cache
- **What**: Docker volume for `node_modules` (line 180 in docker-compose.yml)
- **When**: Dependencies are installed
- **Fix**: Delete volume: `docker compose down -v`

### 4. Vite Build Cache
- **What**: Vite caches build artifacts in `node_modules/.vite`
- **When**: During development and building
- **Fix**: `rm -rf frontend/node_modules/.vite`

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
npm run dev
```

## Docker Compose Volume Strategy

Current setup (lines 175-179 in `docker-compose.yml`):

```yaml
volumes:
  - ./frontend/src:/app/src:ro          # Source files (read-only)
  - ./frontend/public:/app/public:ro    # Public assets (read-only)
  - ./frontend/package.json:/app/package.json:ro
  - ./frontend/vite.config.ts:/app/vite.config.ts:ro
  - ./frontend/tsconfig.json:/app/tsconfig.json:ro
  - frontend_node_modules:/app/node_modules  # Named volume for node_modules
```

**`:ro` = read-only**: The container can read files but changes in container don't affect host.

## Troubleshooting Checklist

If you see old code:

- [ ] Stop containers: `docker compose down`
- [ ] Clean Vite cache: `rm -rf frontend/node_modules/.vite`
- [ ] Clean dist: `rm -rf frontend/dist`
- [ ] Rebuild containers: `docker compose up --build`
- [ ] Hard refresh browser: `Cmd+Shift+R` or `Ctrl+Shift+R`
- [ ] Check Docker logs: `docker compose logs -f frontend`
- [ ] Verify files changed: `ls -la frontend/src/components/Navigation.tsx`

## New Makefile Commands

```bash
# Quick container rebuild (frontend only)
make docker-rebuild-frontend

# Full clean restart (all containers)
make docker-restart

# Stop all containers
make docker-stop

# View logs
docker compose logs -f frontend
docker compose logs -f backend
```

## Verifying Changes Applied

### Check if file exists in container:
```bash
docker compose exec frontend ls -la /app/src/components/Navigation.tsx
```

### Check container logs for rebuild:
```bash
docker compose logs frontend | grep "Building"
```

### Force complete rebuild (nuclear option):
```bash
docker compose down -v  # Delete all volumes
docker compose build --no-cache  # Ignore all caches
docker compose up
```

## Best Practices

1. **For frontend development**: Use local `npm run dev` for faster iteration
2. **For integration testing**: Use Docker to test complete system
3. **Before commits**: Test with Docker to ensure production-like behavior
4. **After pulling changes**: Run `make docker-restart` to get clean state

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
