FROM python:3.11-slim

WORKDIR /app

COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/src /app/backend/src
COPY shared/schemas /app/shared/schemas
COPY shared/examples /app/shared/examples

RUN pip install --no-cache-dir /app/backend

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "biovolt_backend.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
