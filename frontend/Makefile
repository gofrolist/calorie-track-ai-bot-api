.DEFAULT_GOAL := help

.PHONY: help dev test lint format check clean

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start Vite dev server
	bun run dev

test: ## Run tests
	bun run test

lint: ## Run ESLint
	bun run lint

format: ## Format with Prettier
	bun run format

check: ## Type-check + lint + format check
	bun run check

clean: ## Clean build artifacts
	rm -rf dist node_modules/.vite
