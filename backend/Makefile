.DEFAULT_GOAL := help

.PHONY: help dev worker test test-unit lint format check clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start dev server with hot reload
	uv run uvicorn calorie_track_ai_bot.main:app --host 0.0.0.0 --port 8000 --reload

worker: ## Start background worker
	uv run python -m calorie_track_ai_bot.workers.estimate_worker

test: ## Run all tests
	uv run pytest -v

test-unit: ## Run unit tests only
	uv run pytest tests/ -v --ignore=tests/integration/

lint: ## Run ruff linter
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

check: ## Lint + typecheck
	uv run ruff check .
	uv run pyright

clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
