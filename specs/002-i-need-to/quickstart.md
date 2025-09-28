# Quickstart Guide: Backend-Frontend Integration & Modern UI/UX Enhancement

## Prerequisites

- Node.js 18+ and npm
- Python 3.11+ and uv
- Supabase CLI (`npm install -g supabase`)
- Docker and Docker Compose
- Git

## Environment Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository-url>
cd calorie-track-ai-bot-api

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
uv sync
```

### 2. Environment Configuration

**Backend Environment (`backend/.env`)**:
```bash
# Supabase Configuration (Local Development)
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your_local_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_local_service_role_key

# Supabase Configuration (Production)
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_ANON_KEY=your_production_anon_key
# SUPABASE_SERVICE_ROLE_KEY=your_production_service_role_key

# Upstash Redis (Production)
REDIS_URL=redis://default:password@your-redis.upstash.io:6379

# Local Redis (Development)
# REDIS_URL=redis://localhost:6379/0

# Tigris Storage Configuration
AWS_ENDPOINT_URL_S3=https://fly.storage.tigris.dev
AWS_ACCESS_KEY_ID=your_tigris_access_key
AWS_SECRET_ACCESS_KEY=your_tigris_secret_key
BUCKET_NAME=your_bucket_name

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token
USE_WEBHOOK=false

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-5-mini

# Logging
LOG_LEVEL=DEBUG
APP_ENV=development
```

**Frontend Environment Variables** (set in Vercel or local):
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000  # Local development
# VITE_API_BASE_URL=https://calorie-track-ai-bot.fly.dev  # Production

VITE_API_TIMEOUT=30000

# Development Features
VITE_ENABLE_DEBUG_LOGGING=true
VITE_ENABLE_ERROR_REPORTING=false
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEV_TOOLS=true

# Telegram Configuration
VITE_TELEGRAM_BOT_NAME=your_bot_name
VITE_TELEGRAM_APP_URL=http://localhost:3000  # Local development
# VITE_TELEGRAM_APP_URL=https://your-app.vercel.app  # Production
```

## Local Development

### 3. Start Development Environment

```bash
# Start Supabase database only (more efficient than full supabase start)
supabase db start

# Start backend with hot reload
cd backend
uv run uvicorn src.calorie_track_ai_bot.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend with hot reload
cd frontend
npm run dev
```

### 4. Database Migrations

```bash
# Apply migrations to local Supabase database
supabase db reset

# Push schema changes to local database instance
supabase db push

# Generate types for TypeScript from local database
supabase gen types typescript --local > frontend/src/types/supabase.ts
```

### 5. Verify Connectivity

```bash
# Test backend health
curl http://localhost:8000/health/live

# Test connectivity endpoint
curl http://localhost:8000/health/connectivity

# Test frontend-backend integration
curl http://localhost:3000/api/health
```

## Testing Integration

### 5. Run Integration Tests

```bash
# Frontend integration tests
cd frontend
npm run test:integration

# Backend integration tests
cd backend
uv run pytest tests/integration/

# Full stack tests
make test-integration
```

### 6. Test Mobile Safe Areas

1. Open browser developer tools
2. Toggle device toolbar
3. Select iPhone/Android device
4. Verify safe areas are respected:
   - Top safe area: `env(safe-area-inset-top)`
   - Bottom safe area: `env(safe-area-inset-bottom)`
   - Left/Right safe areas: `env(safe-area-inset-left/right)`

### 7. Test Theme and Language Detection

```bash
# Test theme detection
curl http://localhost:8000/api/v1/config/theme

# Test language detection
curl http://localhost:8000/api/v1/config/language

# Test CORS preflight
curl -X OPTIONS http://localhost:8000/api/v1/config/ui \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Content-Type"

# Should return CORS headers
```

## UI/UX Validation

### 8. Test Modern UI Components

1. **Theme Detection**:
   - Automatic theme detection from Telegram WebApp API (`webApp.colorScheme`)
   - System preference detection (`prefers-color-scheme`)
   - Manual theme override capability
   - Verify Telegram theme integration
   - Check CSS custom properties update

2. **Language Detection**:
   - Automatic language detection from Telegram user data (`webApp.initDataUnsafe.user.language_code`)
   - Browser language fallback (`navigator.language`)
   - Supported languages validation
   - i18n integration testing

3. **Responsive Design**:
   - Test different screen sizes
   - Verify mobile-first approach
   - Check touch interactions

4. **Safe Areas**:
   - Test on devices with notches
   - Verify content doesn't overlap system UI
   - Check landscape/portrait orientations

### 9. Test Feature Flags

```bash
# Test feature flag API
curl http://localhost:8000/api/v1/config/ui | jq '.features'

# Update feature flags
curl -X PUT http://localhost:8000/api/v1/config/ui \
  -H "Content-Type: application/json" \
  -d '{"features": {"enableDebugLogging": true}}'
```

## Logging System

### 10. Test Structured Logging

```bash
# Submit log entry
curl -X POST http://localhost:8000/api/v1/logs \
  -H "Content-Type: application/json" \
  -d '{
    "level": "INFO",
    "service": "frontend",
    "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
    "message": "User action performed",
    "context": {"action": "test"},
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
  }'

# Check logs
docker logs calorie-track-backend
```

## Performance Testing

### 11. Test Performance Metrics

```bash
# Test API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health/connectivity

# Test frontend load times
npm run test:performance

# Monitor resource usage
make monitor-resources
```

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Check backend CORS configuration
   - Verify frontend origin matches allowed origins
   - Ensure preflight requests are handled

2. **Safe Area Issues**:
   - Verify CSS `env()` functions are supported
   - Check device-specific safe area values
   - Test on actual mobile devices

3. **Connectivity Issues**:
   - Check network connectivity
   - Verify API endpoints are accessible
   - Review error logs for details

4. **Performance Issues**:
   - Monitor CPU/memory usage
   - Check for memory leaks
   - Optimize bundle sizes

### Debug Commands

```bash
# Check service status
make status

# View logs
make logs

# Restart services
make restart

# Clean environment
make clean
```

## Production Deployment

### 12. Build for Production

```bash
# Build frontend
cd frontend
npm run build

# Build backend
cd backend
uv run ruff check
uv run pyright
```

### 13. Deploy to Production

```bash
# Deploy backend to Fly.io
cd backend
fly deploy

# Deploy frontend to Vercel
cd frontend
vercel --prod

# Push database migrations to production Supabase
supabase db push --project-ref your-project-ref
```

## Success Criteria

✅ **Connectivity**: Frontend successfully connects to backend without CORS errors
✅ **Safe Areas**: Mobile safe areas properly respected on all devices
✅ **UI/UX**: Modern Telegram WebApp design implemented
✅ **Logging**: Structured logging system operational
✅ **Development**: Local development environment works seamlessly
✅ **Performance**: CPU/memory usage optimized
✅ **Documentation**: Architecture and integration docs up-to-date

## Next Steps

1. **Monitor Performance**: Track response times and resource usage
2. **User Testing**: Test on real mobile devices
3. **Documentation**: Update user guides and API docs
4. **Monitoring**: Set up production monitoring and alerting
5. **Optimization**: Continue performance improvements
