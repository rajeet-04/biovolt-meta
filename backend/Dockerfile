FROM python:3.11-slim

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/src /app/backend/src
COPY shared/schemas /app/shared/schemas
COPY shared/examples /app/shared/examples

ENV PYTHONPATH=/app/backend/src

RUN pip install --no-cache-dir /app/backend

RUN useradd --create-home --uid 10001 biovolt && mkdir -p /data/exports && chown -R biovolt:biovolt /data /app
COPY backend/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 755 /usr/local/bin/docker-entrypoint.sh
USER biovolt

WORKDIR /app/backend

EXPOSE 8000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "biovolt_backend.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
