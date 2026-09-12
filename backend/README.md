# Backend

Planned owner: FastAPI service.

Responsibilities beginning in Phase 1:

- device WebSocket gateway
- dashboard WebSocket gateway
- server timestamps
- scientific derived metrics
- experiment lifecycle
- calibration profiles
- SQLite persistence
- CSV export

Phase 0 contains no backend runtime code.

## Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
cp ../.env.example .env
# Replace BIOVOLT_DEVICE_SHARED_TOKEN in .env before running the service.
python -m pip install -e '.[dev]'
pytest -v
ruff check .
ruff format --check .
uvicorn biovolt_backend.main:app --reload --app-dir src
```

## Docker

Build the image from the repository root so the Dockerfile can copy the
backend package using its root-context paths:

```bash
docker build -f backend/Dockerfile -t biovolt-backend:phase1 .
```

Run the standalone development container with its token and database path
provided at runtime:

```bash
docker run --rm -p 8000:8000 \
  -e BIOVOLT_DEVICE_SHARED_TOKEN=replace-with-a-device-token \
  -e BIOVOLT_DATABASE_URL=sqlite+aiosqlite:////tmp/biovolt.db \
  biovolt-backend:phase1
```

The service is then available at `http://localhost:8000`; its health check is
`http://localhost:8000/api/health`.
