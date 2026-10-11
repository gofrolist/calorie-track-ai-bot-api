# Tests for Calorie Track AI Bot API

This directory contains comprehensive tests for all Python modules in the calorie tracking AI bot API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures; sets test env vars and mocks external services
├── test_main.py             # Tests for main FastAPI application
├── api/
│   └── v1/
│       ├── test_bot.py, test_bot_inline.py           # Telegram webhook / inline mode
│       ├── test_config_language.py, test_config_theme.py,
│       │   test_config_ui_get.py, test_config_ui_put.py  # /api/v1/config/*
│       ├── test_daily_summary.py                     # Daily/weekly/monthly summaries
│       ├── test_dev_environment.py                   # /api/v1/dev/*
│       ├── test_estimates.py                         # Estimate endpoints
│       ├── test_feedback.py                          # Feedback endpoints
│       ├── test_goals.py                             # Goal endpoints
│       ├── test_inline_analytics_endpoint.py         # Inline analytics
│       ├── test_logs.py                              # Frontend log ingestion
│       ├── test_meals.py, test_meals_calendar.py, test_meals_delete.py,
│       │   test_meals_get.py, test_meals_list.py, test_meals_update.py,
│       │   test_meals_user_id.py                     # Meal endpoints
│       └── test_photos.py, test_photos_multiphotos.py  # Photo upload endpoints
├── integration/
│   ├── test_inline_flows.py # Inline mode end-to-end flows (mocked services)
│   └── test_photo_urls.py   # Photo URL generation
├── services/
│   ├── test_db.py           # Tests for database service
│   ├── test_estimator.py, test_estimator_multiphotos.py  # AI estimation service
│   ├── test_feedback_service.py
│   ├── test_inline_notifications.py, test_inline_observability.py
│   ├── test_monitoring.py
│   ├── test_photo_limit.py, test_photo_validation.py
│   ├── test_queue.py        # Tests for Redis queue service
│   ├── test_storage.py      # Tests for S3/Tigris storage service
│   └── test_telegram_media_groups.py
└── workers/
    └── test_estimate_worker.py # Tests for background worker
```

## Running Tests

All external services (database, Redis, OpenAI, S3, Telegram) are mocked in `conftest.py`, and test environment variables are set there automatically, so no credentials or running services are needed. Run from `backend/`:

```bash
make test        # All tests (uv run pytest -v)
make test-unit   # Excludes tests/integration/

# Specific file or test
uv run pytest tests/services/test_estimator.py -v
uv run pytest tests/api/v1/test_meals.py::test_name
```

## Test Coverage

### Services Tests
- **db**: Database operations with mocked psycopg3 pool
- **estimator.py**: AI estimation with mocked OpenAI client
- **queue.py**: Redis queue operations with mocked Redis client
- **storage.py**: S3/Tigris operations with mocked boto3 client
- **feedback_service.py, monitoring.py, inline_notifications.py, telegram.py**: Feedback, monitoring, inline mode and media group handling

### API Tests
- **bot.py**: Telegram webhook and inline mode
- **config.py**: UI configuration, theme and language detection
- **photos.py**: Photo upload endpoints (single and multi-photo)
- **estimates.py**: Estimation request endpoints
- **meals.py**: Meal create/list/calendar/get/update/delete endpoints
- **goals.py, daily_summary.py, feedback.py, logs.py, dev.py, inline_analytics.py**: Remaining API routers

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
- `pytest-cov`: Coverage reports
- `unittest.mock`: Mocking framework
- `fastapi.testclient`: FastAPI testing utilities

## Environment Variables

`conftest.py` sets mock environment variables (via `os.environ`, before app imports) to avoid requiring real service credentials:
- `DATABASE_URL`: Mock PostgreSQL connection URL
- `OPENAI_API_KEY`: Mock OpenAI API key
- `REDIS_URL`: Mock Redis URL
- `AWS_*`: Mock Tigris/S3 credentials
- `APP_ENV`: `dev`

## Contributing

When adding new features:
1. Write tests for new functions/endpoints
2. Ensure tests pass with `make test`
3. Run linting with `uv run ruff check tests/`
4. Update this README if adding new test categories
