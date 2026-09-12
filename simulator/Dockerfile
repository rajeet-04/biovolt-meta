FROM python:3.11-slim

WORKDIR /app

COPY simulator/pyproject.toml /app/simulator/pyproject.toml
COPY simulator/src /app/simulator/src

RUN pip install --no-cache-dir /app/simulator

WORKDIR /app/simulator

ENTRYPOINT ["biovolt-simulator"]
