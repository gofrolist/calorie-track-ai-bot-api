SHELL := /usr/bin/env bash
export PYTHONUNBUFFERED=1

.PHONY: help
help:
	@echo "Targets:"
	@echo "  sync           - Install project deps with uv"
	@echo "  precommit      - Run pre-commit on all files"
	@echo "  run            - Start bot locally (polling)"
	@echo "  test           - Run tests"
	@echo "  build          - Build Docker image"
	@echo "  deploy         - Deploy to Fly using GHCR image (requires FLY_API_TOKEN)"

.PHONY: sync
sync:
	uv sync --all-extras

.PHONY: precommit
precommit:
	uv run pre-commit autoupdate
	uv run pre-commit install-hooks
	uv run pre-commit run --all-files

.PHONY: run
run:
	uv run uvicorn calorie_track_ai_bot.main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: test
test:
	uv run pytest

IMAGE ?= ghcr.io/${USER}/calorie_track_ai_bot:dev
REGION ?= lax

.PHONY: build
build:
	docker build --platform linux/arm64 -t $(IMAGE) .

.PHONY: deploy
deploy:
	flyctl deploy --image $(IMAGE) --remote-only
