# Tests for Calorie Track AI Bot API

This directory contains comprehensive tests for all Python modules in the calorie tracking AI bot API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared test fixtures and configuration
├── test_main.py             # Tests for main FastAPI application
├── api/
│   └── v1/
│       ├── test_auth.py     # Tests for authentication endpoints
│       ├── test_estimates.py # Tests for estimate endpoints
│       ├── test_health.py   # Tests for health check endpoints
│       ├── test_meals.py     # Tests for meal endpoints
│       └── test_photos.py    # Tests for photo endpoints
├── services/
│   ├── test_config.py       # Tests for configuration module
│   ├── test_db.py          # Tests for database service
│   ├── test_estimator.py   # Tests for AI estimation service
│   ├── test_queue.py       # Tests for Redis queue service
│   └── test_storage.py     # Tests for S3/Tigris storage service
└── workers/
    └── test_estimate_worker.py # Tests for background worker
```

## Running Tests

### Quick Test Run (Recommended)
Run tests that don't require external services:
```bash
./run_tests.sh
```

### Manual Test Run
Set environment variables and run specific tests:
```bash
export SUPABASE_URL="https://test.supabase.co"
export SUPABASE_SERVICE_ROLE="test-supabase-key"
export OPENAI_API_KEY="sk-test123"
export REDIS_URL="redis://localhost:6379"
export TIGRIS_ENDPOINT="https://test.tigris.com"
export TIGRIS_ACCESS_KEY="test-access-key"
export TIGRIS_SECRET_KEY="test-secret-key"
export TIGRIS_BUCKET="test-bucket"

uv run pytest tests/services/test_config.py tests/api/v1/test_health.py tests/api/v1/test_auth.py -v
```

### All Tests (Requires External Services)
To run all tests, you need access to:
- Supabase instance
- Redis server
- Tigris/S3 storage
- OpenAI API key

```bash
uv run pytest tests/ -v
```

## Test Coverage

### Services Tests
- **config.py**: Environment variable handling and defaults
- **db.py**: Database operations with mocked Supabase client
- **estimator.py**: AI estimation with mocked OpenAI client
- **queue.py**: Redis queue operations with mocked Redis client
- **storage.py**: S3/Tigris operations with mocked boto3 client

### API Tests
- **health.py**: Health check endpoints
- **auth.py**: Authentication endpoints
- **photos.py**: Photo upload endpoints
- **estimates.py**: Estimation request endpoints
- **meals.py**: Meal creation endpoints

### Worker Tests
- **estimate_worker.py**: Background job processing

### Main Application Tests
- **test_main.py**: FastAPI app configuration and routing

## Test Features

- **Comprehensive Coverage**: Tests cover all public functions and endpoints
- **Mocking**: External dependencies are mocked to avoid requiring actual services
- **Error Handling**: Tests verify proper error handling and edge cases
- **Type Safety**: Tests validate input/output types and data structures
- **Async Support**: Full support for async/await patterns
- **Fixtures**: Shared test fixtures for common setup

## Test Dependencies

The tests use the following testing libraries:
- `pytest`: Main testing framework
- `pytest-asyncio`: Async test support
- `unittest.mock`: Mocking framework
- `fastapi.testclient`: FastAPI testing utilities

## Environment Variables

Tests use mock environment variables to avoid requiring real service credentials:
- `SUPABASE_URL`: Mock Supabase URL
- `SUPABASE_SERVICE_ROLE`: Mock Supabase key
- `OPENAI_API_KEY`: Mock OpenAI API key
- `REDIS_URL`: Mock Redis URL
- `TIGRIS_*`: Mock Tigris/S3 credentials

## Contributing

When adding new features:
1. Write tests for new functions/endpoints
2. Ensure tests pass with `./run_tests.sh`
3. Run linting with `uv run ruff check tests/`
4. Update this README if adding new test categories
