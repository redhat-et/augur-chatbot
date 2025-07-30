FROM python:3.12-slim as base




FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
# Set the working directory inside the container
WORKDIR /app
COPY uv.lock pyproject.toml /app
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev

FROM base
WORKDIR /app
COPY --from=builder /app /app
ENV PATH="/app/.venv/bin:$PATH"


# Explicitly tell Python where to find packages
ENV PYTHONPATH="/app/.venv/lib/python3.9/site-packages:/app"

COPY ./data /app/data

# Copy all the python scripts into the working directory
COPY *.py ./
