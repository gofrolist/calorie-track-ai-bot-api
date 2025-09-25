SHELL := /usr/bin/env bash
export PYTHONUNBUFFERED=1

# Default target
.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "Calorie Track AI Bot - Development Commands"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup     - Complete setup (backend + frontend)"
	@echo "  make dev       - Start both backend and frontend in development mode"
	@echo "  make test      - Run all tests (backend + frontend)"
	@echo "  make supabase  - Start Supabase local development"
	@echo ""
	@echo "Available Commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: setup
setup: setup-backend setup-frontend ## Complete setup for development (backend + frontend)
	@echo "Setup complete! Run 'make dev' to start development servers."

.PHONY: setup-backend
setup-backend: ## Setup backend dependencies and environment
	@echo "Setting up backend..."
	@cd backend && make venv
	@echo "Please create backend/.env file with your service credentials if needed"

.PHONY: setup-frontend
setup-frontend: ## Setup frontend dependencies
	@echo "Setting up frontend..."
	@cd frontend && npm install

.PHONY: dev
dev: ## Start both backend and frontend in development mode
	@echo "Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:5173"
	@echo "Press Ctrl+C to stop both servers"
	@$(MAKE) -j2 dev-backend dev-frontend

.PHONY: dev-backend
dev-backend: ## Start backend development server
	@cd backend && make run

.PHONY: dev-frontend
dev-frontend: ## Start frontend development server
	@cd frontend && npm run dev

.PHONY: test
test: test-backend test-frontend ## Run all tests (backend + frontend)

.PHONY: test-backend
test-backend: ## Run backend tests
	@cd backend && make test

.PHONY: test-frontend
test-frontend: ## Run frontend tests
	@cd frontend && npm test

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests
	@cd frontend && npm run test:e2e

.PHONY: lint
lint: lint-backend lint-frontend ## Run linting for both backend and frontend

.PHONY: lint-backend
lint-backend: ## Run backend linting
	@cd backend && make lint && make typecheck

.PHONY: lint-frontend
lint-frontend: ## Run frontend linting
	@cd frontend && npm run build

.PHONY: build
build: build-backend build-frontend ## Build both backend and frontend

.PHONY: build-backend
build-backend: ## Build backend
	@cd backend && make codegen

.PHONY: build-frontend
build-frontend: ## Build frontend for production
	@cd frontend && npm run build

.PHONY: clean
clean: clean-backend clean-frontend ## Clean up temporary files and caches

.PHONY: clean-backend
clean-backend: ## Clean backend temporary files
	@cd backend && make clean

.PHONY: clean-frontend
clean-frontend: ## Clean frontend temporary files
	@cd frontend && rm -rf dist node_modules/.vite

.PHONY: validate
validate: validate-backend validate-frontend ## Validate both backend and frontend

.PHONY: validate-backend
validate-backend: ## Validate backend OpenAPI spec
	@cd backend && make validate

.PHONY: validate-frontend
validate-frontend: ## Validate frontend build
	@cd frontend && npm run build

.PHONY: check-deps
check-deps: ## Check if all required dependencies are installed
	@command -v node >/dev/null 2>&1 || { echo "Node.js is not installed"; exit 1; }
	@command -v npm >/dev/null 2>&1 || { echo "npm is not installed"; exit 1; }
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "Python 3 is not installed"; exit 1; }

.PHONY: health-check
health-check: ## Check if backend is running and healthy
	@curl -f http://localhost:8000/health/live >/dev/null 2>&1 && \
		echo "Backend is healthy" || \
		echo "Backend is not responding"

.PHONY: logs
logs: ## Show logs from both backend and frontend (if running)
	@echo "Backend logs (if running with make dev-backend)"
	@echo "Frontend logs (if running with make dev-frontend)"

.PHONY: docker-dev
docker-dev: ## Start development environment with Docker
	@cd backend && docker compose up --build

.PHONY: docker-stop
docker-stop: ## Stop Docker containers
	@cd backend && docker compose down

.PHONY: telegram-setup
telegram-setup: ## Setup Telegram webhook (requires running backend)
	@curl -X POST http://localhost:8000/bot/setup

.PHONY: telegram-info
telegram-info: ## Get Telegram webhook information
	@curl http://localhost:8000/bot/webhook-info

.PHONY: api-docs
api-docs: ## Open API documentation in browser
	@open http://localhost:8000/docs 2>/dev/null || \
		xdg-open http://localhost:8000/docs 2>/dev/null || \
		echo "Please open http://localhost:8000/docs in your browser"

.PHONY: frontend-preview
frontend-preview: ## Preview built frontend
	@cd frontend && npm run preview

.PHONY: install-deps
install-deps: ## Install all dependencies (backend + frontend)
	@$(MAKE) setup-backend setup-frontend

# Development workflow shortcuts
.PHONY: quick-start
quick-start: check-deps install-deps ## Quick start for new developers
	@echo "Quick start complete!"
	@echo "Next steps:"
	@echo "1. Create backend/.env with your service credentials"
	@echo "2. Run 'make dev' to start development servers"
	@echo "3. Visit http://localhost:8000/docs for API docs"
	@echo "4. Visit http://localhost:5173 for the frontend"

.PHONY: restart
restart: ## Restart development servers
	@pkill -f "uvicorn.*calorie_track_ai_bot" || true
	@pkill -f "vite.*dev" || true
	@sleep 2
	@$(MAKE) dev

.PHONY: supabase
supabase: ## Start Supabase local development
	@echo "Starting Supabase local development..."
	@supabase start
	@echo "Supabase is running at:"
	@echo "  API URL: http://localhost:54321"
	@echo "  Studio: http://localhost:54323"
	@echo "  DB URL: postgresql://postgres:postgres@localhost:54322/postgres"

.PHONY: supabase-stop
supabase-stop: ## Stop Supabase local development
	@supabase stop

.PHONY: supabase-reset
supabase-reset: ## Reset Supabase local database
	@supabase db reset

.PHONY: supabase-gen-types
supabase-gen-types: ## Generate TypeScript types from Supabase
	@supabase gen types typescript --local > types.gen.ts
	@echo "TypeScript types generated in types.gen.ts"

.PHONY: supabase-deploy
supabase-deploy: ## Deploy migrations to production (requires SUPABASE_ACCESS_TOKEN, PRODUCTION_DB_PASSWORD, PRODUCTION_PROJECT_ID)
	@echo "Deploying migrations to production..."
	@supabase link --project-ref $${PRODUCTION_PROJECT_ID}
	@supabase db push
	@echo "Migrations deployed successfully!"
