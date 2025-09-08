#!/bin/bash

# Test runner script for calorie-track-ai-bot-api
# This script sets up the necessary environment variables and runs tests

echo "Setting up test environment..."

# Set test environment variables
export SUPABASE_URL="https://test.supabase.co"
export SUPABASE_SERVICE_ROLE="test-supabase-key"
export OPENAI_API_KEY="sk-test123"
export REDIS_URL="redis://localhost:6379"
export TIGRIS_ENDPOINT="https://test.tigris.com"
export TIGRIS_ACCESS_KEY="test-access-key"
export TIGRIS_SECRET_KEY="test-secret-key"
export TIGRIS_BUCKET="test-bucket"

echo "Running tests that don't require external services..."

# Run tests that work without external dependencies
uv run pytest tests/services/test_config.py tests/api/v1/test_health.py tests/api/v1/test_auth.py -v

echo "Test run completed!"
echo ""
echo "Note: Some tests require external services (Supabase, Redis, etc.) and may fail"
echo "in environments where these services are not available. The tests above validate"
echo "the core functionality that can be tested without external dependencies."
