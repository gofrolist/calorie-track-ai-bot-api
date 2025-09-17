SHELL := /usr/bin/env bash
export PYTHONUNBUFFERED=1

.PHONY: help
help:
	@echo "Backend Targets:"
	@echo "  venv           - Install project deps with uv"
	@echo "  precommit      - Run pre-commit on all files"
	@echo "  run            - Start bot locally (polling)"
	@echo "  lint           - Run ruff linter"
	@echo "  typecheck      - Run pyright type checker"
	@echo "  test           - Run tests"
	@echo "  validate       - Validate OpenAPI spec"
	@echo "  codegen        - Generate schemas from OpenAPI spec"
	@echo "  clean          - Clean up temporary files and caches"

.PHONY: venv
venv:
	uv sync --all-extras

.PHONY: precommit
precommit:
	uv run pre-commit autoupdate
	uv run pre-commit install-hooks
	uv run pre-commit install --hook-type pre-commit --hook-type pre-push -f
	uv run pre-commit run --all-files

.PHONY: run
run:
	uv run uvicorn calorie_track_ai_bot.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: lint
lint:
	uv run ruff check

.PHONY: typecheck
typecheck:
	uv run pyright

.PHONY: test
test:
	uv run pytest

.PHONY: validate
validate:
	uv run openapi-spec-validator specs/openapi.yaml

.PHONY: codegen
codegen:
	uv run datamodel-codegen \
		--input specs/openapi.yaml \
		--input-file-type openapi \
		--output src/calorie_track_ai_bot/schemas.py \
		--output-model-type pydantic_v2.BaseModel \
		--target-python-version 3.12

.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
