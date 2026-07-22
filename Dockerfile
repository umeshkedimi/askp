# syntax=docker/dockerfile:1
FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install dependencies first, in their own layer, so an app-code-only change
# doesn't invalidate the (slow) dependency-install cache.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.13-slim

RUN groupadd --system askp && useradd --system --gid askp askp

COPY --from=builder --chown=askp:askp /app /app

ENV PATH="/app/.venv/bin:${PATH}" \
    ASKP_HOST=0.0.0.0 \
    ASKP_PORT=8000

WORKDIR /app
USER askp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["askp", "serve"]
