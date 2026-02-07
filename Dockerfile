FROM python:3.14-slim@sha256:486b8092bfb12997e10d4920897213a06563449c951c5506c2a2cfaf591c599f AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

FROM base AS deps

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:78a7ff97cd27b7124a5f3c2aefe146170793c56a1e03321dd31a289f6d82a04f /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

FROM base AS final

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gettext \
    libcairo2 \
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

HEALTHCHECK --interval=5s --timeout=5s --start-period=5s --retries=30 \
    CMD curl --fail http://localhost:8000/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--chdir", "src", "--access-logfile", "-"]
