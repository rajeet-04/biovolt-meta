# BioVolt

BioVolt is an adaptive living biophotovoltaic research prototype for MetaMorph 2.0.

## Architecture

- ESP32: sensing, local safety, actuation, Perturb & Observe control
- FastAPI: scientific derivations, experiments, persistence, WebSockets
- React PWA: visualization and operator interaction

## Repository Areas

- `firmware/esp32/`
- `backend/`
- `frontend/`
- `simulator/`
- `shared/`
- `docs/`
- `scripts/`
- `tests/`

## Current Development Phase

Phase 1: backend, simulator, persistence, and integration development.

## Docker Compose Development Stack

The root Compose file runs the backend by default. It stores SQLite data in
the named `biovolt-data` volume and reads the device token from
`BIOVOLT_DEVICE_SHARED_TOKEN`; no token is committed to the repository.

Prepare local configuration once:

```bash
cp .env.example .env
# Replace BIOVOLT_DEVICE_SHARED_TOKEN in .env with a long random token.
```

Start only the backend and check its health endpoint:

```bash
docker compose up --build -d backend
curl http://localhost:8000/api/health
```

The simulator is opt-in through the `simulator` profile. Start both services
and inspect the connected-device status with:

```bash
docker compose --profile simulator up --build -d
curl http://localhost:8000/api/system/status
```

The optional `BIOVOLT_BPW34_DARK_RAW` and `BIOVOLT_BPW34_BLANK_RAW` settings
should remain commented out when unused. Compose passes those values only when
they are defined, avoiding blank strings that strict Pydantic float settings
cannot parse. Stop and restart services without `docker compose down -v` to
keep persisted telemetry; `down -v` intentionally removes the named volume.

## Scientific Ownership Rule

Raw ESP32 telemetry contains measured/control-state values only. Current, power, OD680, biomass, estimated CO2 biofixed into biomass, cumulative energy, and server timestamps are derived by the backend.
