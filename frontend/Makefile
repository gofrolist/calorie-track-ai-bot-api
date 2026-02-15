.DEFAULT_GOAL := help

.PHONY: help dev test lint format check clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start Vite dev server
	npm run dev

test: ## Run tests
	npm test

lint: ## Run ESLint
	npm run lint

format: ## Format with Prettier
	npm run format

check: ## Type-check + lint + format check
	npm run check

clean: ## Clean build artifacts
	rm -rf dist node_modules/.vite
