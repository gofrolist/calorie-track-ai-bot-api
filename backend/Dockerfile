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

FROM python:3.12.11-alpine AS development

WORKDIR /app

# Install development dependencies
RUN apk add --no-cache tzdata curl

ENV TZ=Etc/UTC

# Copy uv from builder stage
COPY --from=builder /bin/uv /bin/uvx /bin/

# Copy source code for development
COPY . /app

# Create virtual environment and install dependencies
RUN uv venv
ENV PATH="/app/.venv/bin:$PATH"

# Install the project in development mode with all dependencies
RUN uv pip install -e .

# Expose port for development
EXPOSE 8000

# Default command for development (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "calorie_track_ai_bot.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM python:3.12.11-alpine AS runtime

WORKDIR /app

RUN apk add --no-cache tzdata
ENV TZ=Etc/UTC

# Copy the environment and necessary files
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Run the application
EXPOSE 8080
CMD ["uvicorn", "calorie_track_ai_bot.main:app", "--host", "0.0.0.0", "--port", "8080"]
