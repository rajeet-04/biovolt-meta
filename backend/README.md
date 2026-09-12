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

The image also contains the canonical shared schemas at `/app/shared/schemas`,
which is the repository root resolved by the backend contract loader. Verify
that image layout and validate a canonical payload with:

```bash
docker run --rm biovolt-backend:phase1 python -c \
  'import json; from pathlib import Path; from biovolt_backend.contracts.loader import validate_payload; payload=json.loads(Path("/app/shared/examples/device-telemetry.example.json").read_text()); validate_payload("device-telemetry.v1.schema.json", payload); print("contract validation: ok")'
```

## Simulator and ESP32 switchover

The simulator is an optional, disposable client for development before
hardware is available. Run the backend without it for a real-device session:

```bash
docker compose stop simulator
docker compose up -d backend
```

Configure the ESP32 to connect to
`ws://<laptop-hotspot-ip>:8000/ws/device` using a unique device ID and the
configured shared token. Hardware uses the same `device-telemetry.v1` schema
and authentication headers as the simulator:

```text
X-BioVolt-Device-ID: <device_id>
Authorization: Bearer <shared-token>
```

No backend feature flag, route, database table, scientific calculation, or
frontend contract selects the source. A hardware run does not require the
simulator package or container.
