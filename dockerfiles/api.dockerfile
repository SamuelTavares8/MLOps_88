FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS base

WORKDIR /app

COPY uv.lock pyproject.toml README.md ./
RUN uv sync --frozen --no-install-project

COPY src src/
COPY models models
RUN uv sync --frozen


# Cloud Run requires this
EXPOSE 8080

# IMPORTANT: shell form so $PORT is expanded
CMD uv run uvicorn src.xray_image_classifier.api:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --workers 1
