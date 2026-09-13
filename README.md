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

Phase 2.1: frontend foundation and application shell. Backend, simulator,
persistence, and integration work from Phase 1 remain available for local
development; frontend backend integration begins in Phase 2.2.

## Frontend Development

The Phase 2.1 frontend is a shell-only React/Vite application. Start it from
the repository root with:

```bash
cd frontend
npm install
npm run dev
```

Run its lint, strict typecheck, tests, and production build before handing off
frontend changes:

```bash
npm run lint
npm run typecheck
npm run test:run
npm run build
```

This phase does not connect the frontend to FastAPI or calculate telemetry;
those integration contracts are added in Phase 2.2.

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

The React PWA preview is opt-in through the `frontend` profile. It builds the
`frontend/Dockerfile` preview server, depends on a healthy backend, and serves
on `http://localhost:4173`. It expects `BIOVOLT_DEVICE_SHARED_TOKEN` to be set
in the environment or `.env`, the same as the backend. Start the backend and
PWA together with:

```bash
docker compose --profile frontend up --build -d
```

Add `--profile simulator` to bring the simulator online alongside the PWA
without restarting the frontend.

The optional `BIOVOLT_BPW34_DARK_RAW` and `BIOVOLT_BPW34_BLANK_RAW` settings
should remain commented out when unused. Compose passes those values only when
they are defined, avoiding blank strings that strict Pydantic float settings
cannot parse. Stop and restart services without `docker compose down -v` to
keep persisted telemetry; `down -v` intentionally removes the named volume.

The simulator is optional, disposable development infrastructure: it unblocks
backend and frontend work before physical hardware is ready and is not needed
for a real-device run. To switch from simulator to ESP32, stop only the
simulator and leave FastAPI running:

```bash
docker compose stop simulator
docker compose up -d backend
```

Configure the ESP32 for `ws://<laptop-hotspot-ip>:8000/ws/device` with a unique
device ID and the configured shared token. Use that same ID in both the
authentication header and the payload's top-level `device_id`; it must send the
same Phase 0 `device-telemetry.v1` JSON schema and authentication headers:
`X-BioVolt-Device-ID: <device_id>` and `Authorization: Bearer <shared-token>`.
The backend route, scientific processing, database, and dashboard contract do
not change. The switchover does not require a simulator install, a simulator
container in the demo, feature flags, or a second telemetry table.

## Phase 2 PWA acceptance checks

With the PWA preview serving on `http://localhost:4173`, follow the operator
checklist in [`scripts/phase2_smoke.md`](scripts/phase2_smoke.md) to verify
live telemetry, simulator removal, and offline/installed-PWA behavior.

## Phase 1 acceptance checks

With the simulator profile running, execute the short smoke check followed by
the manual 30-minute soak gate:

```bash
docker compose --profile simulator up --build -d
python scripts/phase1_smoke.py
python scripts/soak_phase1.py --minutes 30
```

The smoke check validates backend health, simulator registration, derived
power, and multiple persisted samples. The soak check polls every 30 seconds,
requires fresh live and persisted telemetry, tolerates a bounded simulator
reconnect, rejects negative cumulative energy, and checks the persisted-row
rate against a 90% to 110% range. The history endpoint is bounded to 1,000
samples; after that window fills, the script verifies its timestamp span remains
between 0.90 and 1.10 Hz. Both scripts are read-only and do not print or accept
device tokens.

## Scientific Ownership Rule

Raw ESP32 telemetry contains measured/control-state values only. Current, power, OD680, biomass, estimated CO2 biofixed into biomass, cumulative energy, and server timestamps are derived by the backend.
