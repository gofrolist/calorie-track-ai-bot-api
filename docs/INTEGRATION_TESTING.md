# Integration Testing Guide

## Overview

This guide provides comprehensive instructions for testing the integration between the frontend and backend components of the Calorie Track AI Bot system. It covers contract testing, API integration, E2E testing, performance validation, and mobile device testing for the Telegram Mini App.

## Integration Test Architecture

```mermaid
graph TB
    subgraph "Test Environment"
        subgraph "Frontend Tests"
            UNIT_FE[Unit Tests<br/>Vitest]
            CONTRACT_FE[Contract Tests<br/>API Validation]
            COMPONENT_FE[Component Tests<br/>React Testing]
            E2E_FE[E2E Tests<br/>Playwright]
        end

        subgraph "Backend Tests"
            UNIT_BE[Unit Tests<br/>Pytest]
            CONTRACT_BE[Contract Tests<br/>API Specs]
            INTEGRATION_BE[Integration Tests<br/>Database & Redis]
            PERFORMANCE_BE[Performance Tests<br/>Load & Stress]
        end

        subgraph "Full Stack Tests"
            CONNECTIVITY[Connectivity Tests<br/>Health Checks]
            WORKFLOW[Workflow Tests<br/>User Journeys]
            MOBILE[Mobile Tests<br/>Device Simulation]
            THEME_LANG[Theme & Language<br/>Detection Tests]
        end

        subgraph "Test Infrastructure"
            VITEST[Vitest + Testing Library]
            PLAYWRIGHT[Playwright Multi-Device]
            PYTEST[Pytest + FastAPI TestClient]
            MOCK[Mock Services & Fixtures]
            SUPABASE[Supabase Test DB]
            DOCKER[Docker Test Containers]
        end
    end

    %% Frontend test connections
    UNIT_FE --> VITEST
    CONTRACT_FE --> VITEST
    COMPONENT_FE --> VITEST
    E2E_FE --> PLAYWRIGHT

    %% Backend test connections
    UNIT_BE --> PYTEST
    CONTRACT_BE --> PYTEST
    INTEGRATION_BE --> PYTEST
    PERFORMANCE_BE --> PYTEST

    %% Full stack test connections
    CONNECTIVITY --> MOCK
    WORKFLOW --> PLAYWRIGHT
    MOBILE --> PLAYWRIGHT
    THEME_LANG --> PLAYWRIGHT

    %% Infrastructure connections
    INTEGRATION_BE --> SUPABASE
    INTEGRATION_BE --> DOCKER
    CONTRACT_BE --> MOCK
```

## Local Testing Setup

### Prerequisites

```mermaid
graph LR
    subgraph "Required Tools"
        NODE[Node.js 18+]
        PYTHON[Python 3.11+]
        DOCKER[Docker]
        POSTGRES[PostgreSQL]
        REDIS[Redis]
    end

    subgraph "Environment Files"
        ENV_FE[.env.frontend]
        ENV_BE[.env.backend]
        ENV_TEST[.env.test]
    end

    NODE --> ENV_FE
    PYTHON --> ENV_BE
    DOCKER --> ENV_TEST
```

### Environment Configuration

#### Frontend Environment (.env.frontend)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000

# Development Features
VITE_ENABLE_DEBUG_LOGGING=true
VITE_ENABLE_ERROR_REPORTING=false
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_DEV_TOOLS=true

# Telegram Configuration (for testing)
VITE_TELEGRAM_BOT_NAME=test_bot
VITE_TELEGRAM_APP_URL=http://localhost:3000

# Production Configuration
# VITE_API_BASE_URL=https://calorie-track-ai-bot.fly.dev
# VITE_ENABLE_DEBUG_LOGGING=false
# VITE_ENABLE_ERROR_REPORTING=true
# VITE_ENABLE_ANALYTICS=true
# VITE_ENABLE_DEV_TOOLS=false
```

#### Backend Environment (.env.backend)
```bash
# Database Configuration
SUPABASE_URL=postgresql://localhost:5432/calorie_track_test
SUPABASE_DB_PASSWORD=test_password

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Storage Configuration (Mock for testing)
AWS_ENDPOINT_URL_S3=http://localhost:9000
AWS_ACCESS_KEY_ID=test_key
AWS_SECRET_ACCESS_KEY=test_secret
BUCKET_NAME=test-bucket

# Telegram Configuration
TELEGRAM_BOT_TOKEN=test_token
USE_WEBHOOK=false

# Logging
LOG_LEVEL=DEBUG
APP_ENV=development
```

## Testing Workflows

### 1. Connectivity Testing

```mermaid
sequenceDiagram
    participant DEV as Developer
    participant FE as Frontend
    participant API as Backend API
    participant DB as Database
    participant REDIS as Redis

    DEV->>FE: Start frontend dev server
    DEV->>API: Start backend server
    FE->>API: Health check request
    API-->>FE: Health status
    FE->>API: Test API endpoint
    API->>DB: Database query
    DB-->>API: Query result
    API->>REDIS: Cache check
    REDIS-->>API: Cache result
    API-->>FE: API response
    FE-->>DEV: Test results
```

### 2. Authentication Flow Testing

```mermaid
sequenceDiagram
    participant TEST as Test Suite
    participant FE as Frontend
    participant API as Backend API
    participant AUTH as Auth Service
    participant DB as Database

    TEST->>FE: Initialize app
    FE->>API: POST /api/v1/auth/telegram/init
    API->>AUTH: Validate init data
    AUTH->>DB: Check/create user
    DB-->>AUTH: User data
    AUTH-->>API: Session token
    API-->>FE: Auth response
    FE->>FE: Store session
    FE->>API: Authenticated request
    API->>AUTH: Validate session
    AUTH-->>API: Valid session
    API-->>FE: Protected resource
    FE-->>TEST: Test passed
```

### 3. Photo Upload Testing

```mermaid
sequenceDiagram
    participant TEST as Test Suite
    participant FE as Frontend
    participant API as Backend API
    participant STORAGE as Storage Service
    participant QUEUE as Queue Service
    participant WORKER as Worker

    TEST->>FE: Upload test photo
    FE->>API: POST /api/v1/photos
    API->>STORAGE: Generate presigned URL
    STORAGE-->>API: Upload URL
    API-->>FE: Photo ID + URL
    FE->>STORAGE: Upload file
    FE->>API: POST /api/v1/photos/{id}/estimate
    API->>QUEUE: Queue estimation
    QUEUE->>WORKER: Process job
    WORKER-->>QUEUE: Job complete
    FE->>API: GET /api/v1/estimates/{id}
    API-->>FE: Estimate results
    FE-->>TEST: Upload test passed
```

### 4. Inline Mode Scenarios

Use these manual and automated checks when validating inline mode end-to-end. Each checklist item maps to automated coverage in `tests/api/v1/test_bot_inline.py` or `tests/integration/test_inline_*`.

- [ ] **Inline query acknowledgement** — Trigger an inline query (`@CalorieTrackAI_bot`) in a private chat and confirm the placeholder message appears within 3 seconds while the JSON response echoes the same `job_id`.
- [ ] **Private inline summary** — Select the inline result and verify the final message includes calories, macronutrients, confidence, and the privacy disclosure from the quickstart guide.
- [ ] **Group reply mention** — Reply to a group photo with `@CalorieTrackAI_bot` and check that both the acknowledgement and result stay threaded via `reply_to_message_id`.
- [ ] **Tagged caption flow** — Post a group photo tagging the bot in the caption; expect the bot to reply inline or DM a fallback with admin guidance if permissions block posting, incrementing `permission_block_count`.
- [ ] **Analytics snapshot** — Query `/api/v1/analytics/inline-summary` and confirm the appropriate `trigger_counts` bucket increments for `inline_query`, `reply_mention`, or `tagged_photo`.
- [ ] **Telemetry verification** — Inspect structured logs/metrics to ensure `trigger_type`, acknowledgement latency, and result latency events were emitted for each exercised flow.

## Test Commands

### Frontend Testing

```bash
# Install dependencies
cd frontend
npm install

# Run unit tests
npm run test

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e

# Start development server
npm run dev

# Build for production
npm run build
```

### Backend Testing

```bash
# Install dependencies
cd backend
uv sync

# Run unit tests
uv run pytest tests/

# Run integration tests
uv run pytest tests/integration/

# Run API tests
uv run pytest tests/api/

# Start development server
uv run uvicorn src.calorie_track_ai_bot.main:app --reload --host 0.0.0.0 --port 8000

# Run linting
uv run ruff check
uv run pyright
```

### Full Stack Testing

```bash
# Start all services
make dev-up

# Run connectivity tests
make test-connectivity

# Run integration tests
make test-integration

# Run performance tests
make test-performance

# Stop all services
make dev-down
```

## Test Scenarios

### 1. Basic Connectivity Test

```typescript
// frontend/tests/integration/connectivity.test.ts
describe('Backend Connectivity', () => {
  test('should connect to backend API', async () => {
    const response = await fetch('/health/live');
    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.status).toBe('ok');
  });

  test('should handle CORS properly', async () => {
    const response = await fetch('/api/v1/health', {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'GET',
      },
    });
    expect(response.headers.get('Access-Control-Allow-Origin')).toBeTruthy();
  });
});
```

### 2. Authentication Integration Test

```typescript
// frontend/tests/integration/auth.test.ts
describe('Authentication Integration', () => {
  test('should authenticate with Telegram init data', async () => {
    const mockInitData = 'user=%7B%22id%22%3A123%7D&auth_date=1234567890';

    const response = await authApi.initTelegramAuth(mockInitData);

    expect(response.session_token).toBeDefined();
    expect(response.user).toBeDefined();
    expect(response.user.telegram_user_id).toBe(123);
  });

  test('should maintain session across requests', async () => {
    // Authenticate first
    const authResponse = await authApi.initTelegramAuth(mockInitData);
    sessionManager.setSession(authResponse.session_token);

    // Make authenticated request
    const response = await mealsApi.getMealsByDate('2025-01-27');
    expect(response).toBeDefined();
  });
});
```

### 3. Photo Upload Integration Test

```typescript
// frontend/tests/integration/photo.test.ts
describe('Photo Upload Integration', () => {
  test('should upload photo and get estimate', async () => {
    const testFile = new File(['test image data'], 'test.jpg', {
      type: 'image/jpeg',
    });

    const { photo, estimateId } = await apiUtils.uploadPhotoAndEstimate(testFile);

    expect(photo.id).toBeDefined();
    expect(estimateId).toBeDefined();

    // Poll for estimate completion
    const estimate = await apiUtils.pollEstimate(estimateId);
    expect(estimate.status).toBe('done');
    expect(estimate.kcal_mean).toBeGreaterThan(0);
  });
});
```

## Performance Testing

### Load Testing Architecture

```mermaid
graph TB
    subgraph "Load Testing"
        K6[K6 Load Tests]
        ARTILLERY[Artillery Tests]
        JMETER[JMeter Tests]
    end

    subgraph "Performance Metrics"
        RESPONSE_TIME[Response Time]
        THROUGHPUT[Throughput]
        ERROR_RATE[Error Rate]
        RESOURCE_USAGE[Resource Usage]
    end

    K6 --> RESPONSE_TIME
    ARTILLERY --> THROUGHPUT
    JMETER --> ERROR_RATE
    RESPONSE_TIME --> RESOURCE_USAGE
    THROUGHPUT --> RESOURCE_USAGE
    ERROR_RATE --> RESOURCE_USAGE
```

### Performance Test Commands

```bash
# Run K6 load tests
k6 run tests/performance/load-test.js

# Run Artillery tests
artillery run tests/performance/artillery-config.yml

# Run JMeter tests
jmeter -n -t tests/performance/api-test.jmx -l results.jtl
```

## Debugging Integration Issues

### Common Issues and Solutions

```mermaid
graph TD
    subgraph "Common Integration Issues"
        CORS_ERROR[CORS Errors]
        AUTH_ERROR[Authentication Errors]
        TIMEOUT_ERROR[Timeout Errors]
        NETWORK_ERROR[Network Errors]
    end

    subgraph "Debugging Tools"
        BROWSER_DEV[Browser DevTools]
        NETWORK_TAB[Network Tab]
        CONSOLE_LOG[Console Logging]
        API_LOGS[API Logs]
    end

    CORS_ERROR --> BROWSER_DEV
    AUTH_ERROR --> CONSOLE_LOG
    TIMEOUT_ERROR --> NETWORK_TAB
    NETWORK_ERROR --> API_LOGS
```

### Debugging Checklist

1. **Check CORS Configuration**
   - Verify allowed origins in backend
   - Check preflight requests
   - Validate headers

2. **Verify Authentication**
   - Check session token storage
   - Validate Telegram init data
   - Test token expiration

3. **Monitor Network Requests**
   - Check request/response headers
   - Verify API endpoints
   - Monitor response times

4. **Check Error Handling**
   - Test error scenarios
   - Verify error messages
   - Check fallback behavior

## Continuous Integration

### CI/CD Pipeline for Integration Tests

```mermaid
graph LR
    subgraph "CI Pipeline"
        COMMIT[Code Commit]
        BUILD[Build Services]
        UNIT[Unit Tests]
        INTEGRATION[Integration Tests]
        E2E[E2E Tests]
        PRODUCTION[Deploy to Production]
    end

    COMMIT --> BUILD
    BUILD --> UNIT
    UNIT --> INTEGRATION
    INTEGRATION --> E2E
    E2E --> PRODUCTION
```

### GitHub Actions Workflow

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Frontend Dependencies
        run: |
          cd frontend
          npm ci

      - name: Install Backend Dependencies
        run: |
          cd backend
          uv sync

      - name: Run Frontend Tests
        run: |
          cd frontend
          npm run test:integration

      - name: Run Backend Tests
        run: |
          cd backend
          uv run pytest tests/integration/

      - name: Run E2E Tests
        run: |
          cd frontend
          npm run test:e2e
```

This comprehensive integration testing guide provides all the tools and procedures needed to ensure reliable communication between your frontend and backend components.
