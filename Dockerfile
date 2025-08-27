# ===== Builder =====
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=2.0.0 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PATH="/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential gcc libpq-dev libffi-dev libssl-dev tzdata \
 && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/

# Если lock старый/несовместим, пересобери его (без dev-группы)
RUN poetry install --without dev --no-root --no-ansi \
 || (poetry lock --no-update || poetry lock; poetry install --without dev --no-root --no-ansi)

COPY app /app/app
COPY alembic.ini /app/alembic.ini

# ===== Runtime =====
FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:${PATH}" \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 tzdata dos2unix openssl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

COPY entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8000
CMD ["/app/entrypoint.sh"]
