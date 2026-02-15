SHELL := /usr/bin/env bash
export PYTHONUNBUFFERED=1

.PHONY: help
help:
	@echo "🚀 Backend Development Commands"
	@echo ""
	@echo "📦 Setup & Dependencies:"
	@echo "  setup          - Complete development environment setup"
	@echo "  venv           - Install project deps with uv"
	@echo "  env            - Copy environment template and show setup instructions"
	@echo ""
	@echo "🏃 Development Server:"
	@echo "  dev            - Start development server with hot reload"
	@echo "  run            - Start bot locally (polling)"
	@echo "  worker         - Start background worker"
	@echo "  all            - Start API server and worker together"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-contracts - Run API contract tests"
	@echo "  test-performance - Run performance tests"
	@echo "  test-watch     - Run tests in watch mode"
	@echo "  coverage       - Generate test coverage report"
	@echo ""
	@echo "🔍 Code Quality:"
	@echo "  lint           - Run ruff linter"
	@echo "  lint-fix       - Run ruff linter with auto-fix"
	@echo "  typecheck      - Run pyright type checker"
	@echo "  format         - Format code with ruff"
	@echo "  check          - Run all quality checks (lint + typecheck)"
	@echo "  precommit      - Run pre-commit on all files"
	@echo ""
	@echo "🗄️ Database & Services:"
	@echo "  db-migrate     - Run database migrations"
	@echo ""
	@echo "🐳 Docker & Compose:"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-dev     - Start development with Docker Compose"
	@echo "  docker-logs    - View Docker Compose logs"
	@echo "  docker-clean   - Clean up Docker containers and volumes"
	@echo ""
	@echo "📊 Monitoring & Health:"
	@echo "  health         - Check all service health"
	@echo "  logs           - View application logs"
	@echo "  monitor        - Monitor application performance"
	@echo "  connectivity   - Test backend-frontend connectivity"
	@echo ""
	@echo "📋 Documentation & OpenAPI:"
	@echo "  docs           - Generate and serve API documentation"
	@echo "  openapi-export - Export OpenAPI spec to JSON from running app"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  build          - Build for production"
	@echo "  deploy-staging - Deploy to staging (if applicable)"
	@echo "  deploy-prod    - Deploy to production"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  clean          - Clean up temporary files and caches"
	@echo "  clean-all      - Clean everything including dependencies"

# =============================================================================
# SETUP & DEPENDENCIES
# =============================================================================

.PHONY: setup
setup: venv env
	@echo "✅ Development environment setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Update .env file with your credentials"
	@echo "2. Set DATABASE_URL in .env to your Neon connection string"
	@echo "3. Run 'make dev' to start the development server"
	@echo "4. Run 'make test' to verify everything is working"

.PHONY: venv
venv:
	@echo "📦 Installing dependencies with uv..."
	uv sync --all-extras

.PHONY: env
env:
	@if [ ! -f .env ]; then \
		echo "📋 Creating .env file from template..."; \
		cp env.template .env; \
		echo "✅ .env file created!"; \
		echo ""; \
		echo "🔧 Please update .env with your credentials:"; \
		echo "   - TELEGRAM_BOT_TOKEN (get from @BotFather)"; \
		echo "   - OPENAI_API_KEY (get from OpenAI)"; \
		echo "   - Configure database and Redis URLs"; \
		echo ""; \
		echo "📖 See env.template for detailed setup instructions"; \
	else \
		echo "✅ .env file already exists"; \
	fi

# =============================================================================
# DEVELOPMENT SERVER
# =============================================================================

.PHONY: dev
dev: venv
	@echo "🚀 Starting development server..."
	@if [ -f .env ]; then \
		uv run dotenv run uvicorn calorie_track_ai_bot.main:app --host 0.0.0.0 --port 8000 --reload; \
	else \
		echo "⚠️  Warning: .env file not found. Using system environment variables only."; \
		uv run uvicorn calorie_track_ai_bot.main:app --host 0.0.0.0 --port 8000 --reload; \
	fi

.PHONY: run
run: dev

.PHONY: worker
worker: venv
	@echo "🔄 Starting background worker..."
	@if [ -f .env ]; then \
		uv run dotenv run python -m calorie_track_ai_bot.workers.estimate_worker; \
	else \
		echo "⚠️  Warning: .env file not found. Using system environment variables only."; \
		uv run python -m calorie_track_ai_bot.workers.estimate_worker; \
	fi

.PHONY: all
all:
	@echo "🚀 Starting API server and worker..."
	@echo "Press Ctrl+C to stop all services"
	@trap 'kill %1 %2 2>/dev/null; exit' INT; \
	make dev & \
	sleep 3 && \
	make worker & \
	wait

# =============================================================================
# TESTING & QUALITY
# =============================================================================

.PHONY: test
test: venv
	@echo "🧪 Running all tests..."
	uv run pytest -v

.PHONY: test-unit
test-unit: venv
	@echo "🧪 Running unit tests..."
	uv run pytest tests/ -v --ignore=tests/integration/

.PHONY: test-integration
test-integration: venv
	@echo "🧪 Running integration tests..."
	uv run pytest tests/integration/ -v

.PHONY: test-contracts
test-contracts: venv
	@echo "🧪 Running API contract tests..."
	uv run pytest tests/api/ -v

.PHONY: test-performance
test-performance: venv
	@echo "🧪 Running performance tests..."
	uv run pytest tests/performance/ -v

.PHONY: test-watch
test-watch: venv
	@echo "🧪 Running tests in watch mode..."
	uv run pytest-watch --runner "pytest -v"

.PHONY: coverage
coverage: venv
	@echo "📊 Generating test coverage report..."
	uv run pytest --cov=calorie_track_ai_bot --cov-report=html --cov-report=term
	@echo "📋 Coverage report generated in htmlcov/"

# =============================================================================
# CODE QUALITY
# =============================================================================

.PHONY: lint
lint: venv
	@echo "🔍 Running linter..."
	uv run ruff check

.PHONY: lint-fix
lint-fix: venv
	@echo "🔧 Running linter with auto-fix..."
	uv run ruff check --fix

.PHONY: typecheck
typecheck: venv
	@echo "🔍 Running type checker..."
	uv run pyright

.PHONY: format
format: venv
	@echo "✨ Formatting code..."
	uv run ruff format

.PHONY: check
check: lint typecheck
	@echo "✅ All quality checks passed!"

.PHONY: precommit
precommit: venv
	@echo "🔧 Setting up pre-commit hooks..."
	uv run pre-commit autoupdate
	uv run pre-commit install-hooks
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push -f
	uv run pre-commit run --all-files

# =============================================================================
# DATABASE & SERVICES
# =============================================================================

.PHONY: db-migrate
db-migrate:
	@echo "🔄 Running database migrations against Neon..."
	@echo "Apply schema from infra/schema.sql via psql or Neon console"

# =============================================================================
# DOCKER & COMPOSE
# =============================================================================

.PHONY: docker-build
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t calorie-track-api .

.PHONY: docker-dev
docker-dev:
	@echo "🐳 Starting development with Docker Compose..."
	cd .. && docker-compose up --build

.PHONY: docker-logs
docker-logs:
	@echo "📋 Viewing Docker Compose logs..."
	cd .. && docker-compose logs -f

.PHONY: docker-clean
docker-clean:
	@echo "🧹 Cleaning up Docker containers and volumes..."
	cd .. && docker-compose down -v
	docker image prune -f

# =============================================================================
# MONITORING & HEALTH
# =============================================================================

.PHONY: health
health:
	@echo "🏥 Checking service health..."
	@curl -f http://localhost:8000/health/live || echo "❌ API server is down"
	@curl -f http://localhost:8000/health/connectivity || echo "❌ Connectivity check failed"

.PHONY: logs
logs:
	@echo "📋 Viewing application logs..."
	@tail -f logs/*.log 2>/dev/null || echo "No log files found"

.PHONY: monitor
monitor:
	@echo "📊 Monitoring application performance..."
	@echo "CPU and Memory usage:"
	@ps aux | grep "uvicorn\|estimate_worker" | grep -v grep

.PHONY: connectivity
connectivity:
	@echo "🔗 Testing backend-frontend connectivity..."
	@curl -s http://localhost:8000/health/connectivity | python -m json.tool

# =============================================================================
# DOCUMENTATION & OPENAPI
# =============================================================================

.PHONY: docs
docs: venv
	@echo "📚 Starting API documentation server..."
	@echo "Visit http://localhost:8000/docs for Swagger UI"
	@echo "Visit http://localhost:8000/redoc for ReDoc"
	@echo "Press Ctrl+C to stop the server"
	@open http://localhost:8000/docs 2>/dev/null || true
	@uv run uvicorn src.calorie_track_ai_bot.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: openapi-export
openapi-export: venv
	@echo "📄 Exporting OpenAPI spec from FastAPI app..."
	uv run python -c "import json; from calorie_track_ai_bot.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
	@echo "✅ Exported to openapi.json"

# =============================================================================
# DEPLOYMENT
# =============================================================================

.PHONY: build
build: venv check test
	@echo "🏗️  Building for production..."
	@echo "✅ All checks passed, ready for deployment!"

.PHONY: deploy-staging
deploy-staging:
	@echo "🚀 Deploying to staging..."
	@echo "⚠️  Staging deployment not configured yet"

.PHONY: deploy-prod
deploy-prod:
	@echo "🚀 Deploying to production..."
	@echo "⚠️  Production deployment not configured yet"

# =============================================================================
# CLEANUP
# =============================================================================

.PHONY: clean
clean:
	@echo "🧹 Cleaning up temporary files and caches..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

.PHONY: clean-all
clean-all: clean
	@echo "🧹 Cleaning everything including dependencies..."
	rm -rf .venv/
	uv cache clean
