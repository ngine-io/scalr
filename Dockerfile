# Single source of truth for the interpreter. Both stages derive from it, so
# the venv built below can never be copied onto a different Python or glibc.
# A named stage is used instead of an ARG because Dependabot does not resolve
# ARG substitution in FROM and would stop updating the base image.
FROM docker.io/python:3.14.6-slim AS base

# Build stage: install the locked dependency set into a self-contained venv.
FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/scalr

WORKDIR /build
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY scalr ./scalr
RUN uv sync --locked --no-dev --no-editable

# Runtime stage: only the venv, no uv and no build context.
FROM base

ENV MPLCONFIGDIR=/tmp \
    PATH="/opt/scalr/bin:$PATH"

COPY --from=builder /opt/scalr /opt/scalr

WORKDIR /app
COPY ./docker/config.yml .

USER 1000

ENTRYPOINT ["scalr-ngine"]
