# Phase 1 Overview: Backend Core and ESP32 Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully testable BioVolt backend data pipeline that accepts Phase 0 raw telemetry over an authenticated WebSocket, derives electrical and optical metrics, persists telemetry to SQLite, broadcasts processed telemetry to dashboard clients, and can be exercised without physical hardware using a deterministic ESP32 simulator.

**Architecture:** FastAPI is the Phase 1 runtime boundary. Raw device messages are validated against the Phase 0 contract, converted into typed domain models, processed by pure scientific calculation functions, accumulated into session energy, selectively persisted at 1 Hz, and broadcast at the incoming 2 Hz cadence. A deterministic Python simulator behaves like an ESP32 and uses the exact raw-device contract.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x async ORM, aiosqlite, jsonschema, websockets, pytest, pytest-asyncio, httpx, ruff, Docker Compose.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Completed and merged Phase 0 contracts in `shared/schemas/`, `shared/examples/`, and `docs/protocols/`.

## Global Constraints

- Phase 1 must consume Phase 0 schemas without silently changing field meaning.
- JSON API fields remain `snake_case`.
- Raw ESP32 telemetry remains measured/control/health data only.
- FastAPI owns wall-clock timestamping and all scientific derived values.
- Current is derived from BPV load voltage and configured precision resistor: `I = V / R`.
- Power is derived as `P = V^2 / R`.
- OD680 is derived from BPW34 sample, dark, and blank readings. Missing valid optical calibration must yield `null`, not a fabricated OD value.
- Biomass and estimated CO2 biofixed remain `null` in Phase 1 unless a valid biomass calibration is explicitly supplied. Full calibration-profile CRUD belongs to a later phase.
- The backend must accept 500 ms telemetry cadence and broadcast processed telemetry at the same cadence.
- SQLite persistence is throttled to approximately 1 record/second/device/cell while every incoming frame still updates live state and cumulative energy.
- Device authentication uses device ID plus shared token. No secrets are committed.
- Dashboard WebSocket is read-only in Phase 1.
- ESP32 real firmware, React/PWA UI, experiment lifecycle, operator PIN flow, Nginx, Cloudflared, and production deployment remain out of Phase 1.
- Docker Compose in Phase 1 is a development/integration runner for backend + optional simulator. Production routing is deferred.

---

## Module Map

### Module 1.1: Backend Foundation and Configuration
Plan: `docs/superpowers/plans/phase_1/phase_1_1.md`

Produces:
- installable/importable backend package
- FastAPI app factory
- typed settings
- `/api/health`
- test database fixture
- backend lint/test commands

### Module 1.2: Contract Adapters and Scientific Calculation Core
Plan: `docs/superpowers/plans/phase_1/phase_1_2.md`

Produces:
- JSON Schema contract loader
- Pydantic raw/processed models aligned with Phase 0
- pure current/power/OD680 functions
- processed telemetry builder
- canonical example compatibility tests

### Module 1.3: SQLite Persistence and Energy Accumulation
Plan: `docs/superpowers/plans/phase_1/phase_1_3.md`

Produces:
- async SQLAlchemy engine/session
- telemetry table
- raw payload audit storage
- per-device/cell energy accumulator
- 1 Hz persistence throttle
- latest/history repository queries

### Module 1.4: Device WebSocket and Dashboard Fanout
Plan: `docs/superpowers/plans/phase_1/phase_1_4.md`

Produces:
- `/ws/device`
- device token authentication
- schema validation on every raw frame
- connection registry
- `/ws/dashboard`
- processed telemetry broadcast
- `/api/system/status`
- stale-device tracking

### Module 1.5: Deterministic ESP32 Simulator
Plan: `docs/superpowers/plans/phase_1/phase_1_5.md`

Produces:
- 500 ms raw telemetry simulator
- scientifically coherent synthetic BPV/OD waveforms
- deterministic seed support
- reconnect behavior
- sensor-failure/null simulation
- malformed-packet test mode

### Module 1.6: Integration, Docker Compose, CI, and Acceptance
Plan: `docs/superpowers/plans/phase_1/phase_1_6.md`

Produces:
- root Docker Compose backend + simulator profile
- backend Dockerfile
- integration tests across WebSocket → processing → SQLite → dashboard
- GitHub Actions backend workflow
- 30-minute soak-test script
- Phase 1 acceptance checklist

---

## Dependency Order

```text
Phase 0 merged
    |
    v
1.1 Backend foundation
    |
    v
1.2 Contract + science core
    |
    v
1.3 SQLite + energy state
    |
    v
1.4 WebSocket gateway + fanout
    |
    v
1.5 ESP32 simulator
    |
    v
1.6 Integration + Docker + CI + soak
```

Modules are intentionally sequential because the WebSocket layer consumes domain models and persistence interfaces, while the simulator must target the final device gateway contract.

## Planned Backend Structure After Phase 1

```text
backend/
├── pyproject.toml
├── Dockerfile
├── README.md
├── src/
│   └── biovolt_backend/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   └── status.py
│       ├── contracts/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   └── models.py
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── electrical.py
│       │   ├── optical.py
│       │   ├── processing.py
│       │   └── energy.py
│       ├── persistence/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── models.py
│       │   └── telemetry_repository.py
│       └── websocket/
│           ├── __init__.py
│           ├── auth.py
│           ├── device_registry.py
│           ├── dashboard_hub.py
│           └── routes.py
└── tests/
    ├── conftest.py
    ├── test_health.py
    ├── contracts/
    ├── domain/
    ├── persistence/
    ├── websocket/
    └── integration/

simulator/
├── pyproject.toml
├── Dockerfile
├── README.md
├── src/
│   └── biovolt_simulator/
│       ├── __init__.py
│       ├── __main__.py
│       ├── config.py
│       ├── generator.py
│       └── client.py
└── tests/

docker-compose.yml
.env.example
.github/workflows/backend.yml
scripts/soak_phase1.py
```

## Phase 1 Runtime Data Flow

```text
Fake ESP32 simulator
  raw device-telemetry.v1 JSON
          |
          v
/ws/device + device auth
          |
          v
Phase 0 JSON Schema validation
          |
          v
Pydantic DeviceTelemetryV1
          |
          v
TelemetryProcessor
  - server UTC timestamp
  - current_ua
  - power_uw
  - optional od680
  - cumulative_energy_mj
          |
          +--------------------+
          |                    |
          v                    v
1 Hz SQLite persistence    2 Hz /ws/dashboard
                               |
                               v
                        future React PWA
```

## Phase 1 Scientific Rules

### Current
For `voltage_mv` and `load_resistance_ohm`:

```text
current_ua = voltage_mv * 1000 / load_resistance_ohm
```

### Power
With voltage represented in millivolts:

```text
power_uw = voltage_mv ** 2 / load_resistance_ohm
```

### Energy
For consecutive powers in microwatts and elapsed seconds:

```text
delta_energy_mj = ((previous_power_uw + current_power_uw) / 2) * dt_seconds / 1000
```

Use trapezoidal integration. Device `uptime_ms` is the primary integration timebase because it is resilient to server scheduling jitter. If uptime decreases, treat it as a device restart and reset the boot-session accumulator.

### OD680
If `sample`, `dark`, and `blank` are valid:

```text
od680 = -log10((sample - dark) / (blank - dark))
```

Return `null` when:
- `blank <= dark`
- `sample <= dark`
- required optical references are absent

Do not silently clamp invalid optical data into plausible OD values.

## Phase 1 REST/WS Surface

### REST

```text
GET /api/health
GET /api/system/status
GET /api/telemetry/latest?device_id=...&cell_id=...
GET /api/telemetry/history?device_id=...&cell_id=...&limit=...
```

Experiment REST endpoints are intentionally deferred.

### WebSocket

```text
/ws/device
/ws/dashboard
```

`/ws/device` requires:

```text
X-BioVolt-Device-ID: biovolt-01
Authorization: Bearer <shared-token>
```

`/ws/dashboard` is read-only in Phase 1.

## Planned Commit Sequence

1. `chore: bootstrap FastAPI backend package`
2. `feat: add telemetry contract adapters and science core`
3. `feat: persist processed telemetry and cumulative energy`
4. `feat: add authenticated device websocket gateway`
5. `feat: add deterministic ESP32 simulator`
6. `test: add Phase 1 integration, Docker, CI and soak checks`

Each commit must pass every test introduced up to that commit.

## Phase 1 Exit Criteria

- [ ] Phase 0 contract validation still passes unchanged.
- [ ] `GET /api/health` returns healthy backend/database state.
- [ ] Canonical raw Phase 0 example is accepted by the backend contract adapter.
- [ ] Malformed raw telemetry is rejected and is not persisted or broadcast.
- [ ] Device WebSocket rejects missing/wrong credentials.
- [ ] Authenticated simulator connects and transmits one frame every 500 ms.
- [ ] Backend computes current and power with unit-tested formulas.
- [ ] Backend computes OD680 only when valid optical references are configured.
- [ ] Cumulative energy uses device uptime and trapezoidal integration.
- [ ] Device restart resets boot-session energy state instead of integrating across invalid negative time.
- [ ] Live processed telemetry is broadcast to dashboard clients at incoming cadence.
- [ ] SQLite stores approximately 1 sample/second/device/cell rather than every 500 ms frame.
- [ ] Raw payload is preserved for audit alongside queryable derived columns.
- [ ] `GET /api/telemetry/latest` returns latest processed data.
- [ ] `GET /api/telemetry/history` returns bounded chronological data.
- [ ] Sensor `null` values remain null and do not become fake zeroes.
- [ ] System status exposes connected device count, device IDs, and latest telemetry age.
- [ ] Simulator can intentionally emit a sensor-null frame and backend handles it.
- [ ] Simulator can intentionally emit malformed JSON/schema data and backend rejects it without disconnecting other clients.
- [ ] Backend + simulator start with Docker Compose.
- [ ] Backend unit/integration tests and Phase 0 contract tests pass in GitHub Actions.
- [ ] A 30-minute simulator soak completes without backend crash and with expected persistence rate.

## Handoff to Phase 2

Phase 2 builds the React/Vite/TypeScript installable PWA against the stable Phase 1 REST and `/ws/dashboard` interfaces. Phase 2 must not reach directly into SQLite or duplicate FastAPI scientific calculations.
