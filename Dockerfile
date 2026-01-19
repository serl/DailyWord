FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

FROM base AS deps

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM base AS final

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash app

COPY --from=deps /app/.venv /app/.venv

COPY src/ ./src/
COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

RUN django-admin collectstatic --noinput
RUN django-admin compilemessages
RUN django-admin check

USER app

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=5s --start-period=5s --retries=10 \
    CMD curl --fail http://localhost:8000/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--chdir", "src"]
