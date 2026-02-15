.DEFAULT_GOAL := help

.PHONY: help dev dev-backend dev-frontend test lint format clean docker-dev docker-stop

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start backend and frontend dev servers
	@$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	@$(MAKE) -C backend dev

dev-frontend:
	@$(MAKE) -C frontend dev

test: ## Run all tests
	@$(MAKE) -C backend test
	@$(MAKE) -C frontend test

lint: ## Lint backend and frontend
	@$(MAKE) -C backend check
	@$(MAKE) -C frontend check

format: ## Format backend and frontend
	@$(MAKE) -C backend format
	@$(MAKE) -C frontend format

clean: ## Clean temporary files
	@$(MAKE) -C backend clean
	@$(MAKE) -C frontend clean

docker-dev: ## Start all services via Docker Compose
	docker compose up --build

docker-stop: ## Stop Docker containers
	docker compose down
