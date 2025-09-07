FROM python:3.12.11-alpine AS builder
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/

ENV UV_LINK_MODE=copy

WORKDIR /app

# Install build dependencies for psutil
RUN apk add --no-cache gcc python3-dev musl-dev linux-headers

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

# Copy the project into the intermediate image
COPY . /app

# Sync the project (this installs all dependencies including Babel)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=cache,target=/root/.cache/pip \
    uv sync --locked --no-editable

FROM python:3.12.11-alpine AS runtime

WORKDIR /app

RUN apk add --no-cache tzdata
ENV TZ=Etc/UTC

# Copy the environment
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
EXPOSE 8080
CMD ["uvicorn", "calorie_track_ai_bot.main:app", "--host", "0.0.0.0", "--port", "8080"]
