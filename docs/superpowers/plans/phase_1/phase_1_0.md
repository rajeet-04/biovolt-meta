# Phase 1 Overview: Backend Core and Replaceable ESP32 Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fully testable BioVolt backend data pipeline that accepts Phase 0 raw telemetry over an authenticated WebSocket, derives electrical and optical metrics, persists telemetry to SQLite, broadcasts processed telemetry to dashboard clients, and can be exercised before hardware is ready using a deterministic simulator that is explicitly replaceable by the real ESP32 without backend changes.

**Architecture:** FastAPI is device-source neutral. Raw device messages are validated against the Phase 0 contract, converted into typed domain models, processed by pure scientific calculation functions, accumulated into session energy, selectively persisted at approximately 1 Hz, and broadcast at incoming cadence. The deterministic Python simulator and the future ESP32 are peers implementing the same `device-telemetry.v1` protocol and the same authenticated `/ws/device` transport.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLAlchemy 2.x async ORM, aiosqlite, jsonschema, websockets, pytest, pytest-asyncio, httpx, ruff, Docker Compose.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Completed and merged Phase 0 contracts in `shared/schemas/`, `shared/examples/`, and `docs/protocols/`.

## Global Constraints

- Phase 1 must consume Phase 0 schemas without silently changing field meaning.
- JSON API fields remain `snake_case`.
- Raw device telemetry remains measured/control/health data only.
- FastAPI owns wall-clock timestamping and scientific derived values.
- Current is derived from BPV load voltage and configured precision resistor: `I = V / R`.
- Power is derived as `P = V^2 / R`.
- OD680 is derived from BPW34 sample, dark, and blank readings. Missing valid optical calibration yields `null`.
- Biomass and estimated CO2 biofixed remain `null` in Phase 1 unless a valid biomass calibration is explicitly supplied. Full calibration-profile CRUD belongs later.
- The simulator defaults to a 500 ms telemetry cadence because that matches the planned ESP32 cadence.
- **The backend must never hard-code a 500 ms interval.** Energy uses actual device `uptime_ms` deltas, and valid jittered/delayed frames must still process correctly.
- SQLite persistence is throttled to approximately 1 record/second/device/cell while every valid incoming frame updates live state and cumulative energy.
- Device authentication uses device ID plus shared token. No secrets are committed.
- Dashboard WebSocket is read-only in Phase 1.
- The backend must not import, depend on, or branch on simulator code or simulator-specific device IDs.
- The shared raw telemetry schema must not add `source_type`, `is_simulated`, or equivalent simulator-only metadata.
- Simulator and real ESP32 use the same `/ws/device` route, authentication headers, and `device-telemetry.v1` payload shape.
- ESP32 real firmware, React/PWA UI, experiment lifecycle, operator PIN flow, Nginx, Cloudflared, and production deployment remain out of Phase 1.
- Docker Compose simulator service is optional test infrastructure and must be stoppable without stopping/rebuilding the backend.

---

## Module Map

### Module 1.1: Backend Foundation and Configuration
Plan: `docs/superpowers/plans/phase_1/phase_1_1.md`

Produces:
- installable/importable backend package
- FastAPI app factory
- typed settings
- `/api/health`
- test configuration
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
- approximately 1 Hz persistence throttle
- latest/history repository queries

### Module 1.4: Device WebSocket and Dashboard Fanout
Plan: `docs/superpowers/plans/phase_1/phase_1_4.md`

Produces:
- `/ws/device`
- device token authentication
- schema validation on every raw frame
- telemetry orchestration service
- connection registry
- `/ws/dashboard`
- processed telemetry broadcast
- `/api/system/status`
- `/api/telemetry/latest`
- `/api/telemetry/history`
- stale-device tracking

### Module 1.5: Deterministic ESP32 Simulator
Plan: `docs/superpowers/plans/phase_1/phase_1_5.md`

Produces:
- deterministic 500 ms raw telemetry generator
- scientifically coherent synthetic BPV/optical waveforms
- deterministic seed support
- reconnect behavior
- sensor-failure/null simulation
- malformed-packet test mode

The simulator is explicitly **test infrastructure**, not a backend dependency or production data source type.

### Module 1.6: Integration, Docker Compose, CI, and Acceptance
Plan: `docs/superpowers/plans/phase_1/phase_1_6.md`

Produces:
- root Docker Compose backend + optional simulator profile
- backend and simulator Dockerfiles
- integration tests across WebSocket -> processing -> SQLite -> dashboard
- GitHub Actions backend workflow
- short smoke test
- 30-minute soak-test script

### Module 1.7: Simulator-to-Real-Hardware Substitution Gate
Plan: `docs/superpowers/plans/phase_1/phase_1_7.md`

Produces:
- backend architecture test forbidding simulator dependencies
- cadence-independence tests using non-500-ms intervals
- generic hardware-like WebSocket parity test that imports no simulator code
- documented simulator-off / ESP32-on switchover procedure
- smoke test parameterized by arbitrary device ID
- explicit acceptance proof that real ESP32 replacement requires no FastAPI, database, scientific-calculation, or dashboard-contract rewrite

---

## Mandatory Dependency Order

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
1.5 Deterministic simulator
    |
    v
1.6 Integration + Docker + CI + soak
    |
    v
1.7 Hardware substitution parity gate
    |
    v
Phase 1 complete
```

**Phase 1 is not complete until Module 1.7 passes.**

---

## Runtime Data Flow

During development:

```text
Deterministic Python simulator
  device-telemetry.v1 JSON
          |
          | same auth + same /ws/device
          v
       FastAPI
          |
          +--> Phase 0 schema validation
          +--> scientific processing
          +--> cumulative energy
          +--> ~1 Hz SQLite persistence
          +--> /ws/dashboard live fanout
```

Later with hardware:

```text
ESP32 firmware
  device-telemetry.v1 JSON
          |
          | same auth + same /ws/device
          v
       FastAPI                 <- unchanged
          |
          +--> same validation
          +--> same scientific processing
          +--> same SQLite
          +--> same /ws/dashboard
```

The simulator replacement operation is intentionally operational:

```text
1. stop simulator
2. keep backend running
3. start/connect ESP32
4. ESP32 authenticates to /ws/device
5. ESP32 sends device-telemetry.v1
6. backend continues unchanged
```

---

## Phase 1 Scientific Rules

### Current

```text
current_ua = voltage_mv * 1000 / load_resistance_ohm
```

### Power

```text
power_uw = voltage_mv ** 2 / load_resistance_ohm
```

### Energy

```text
delta_energy_mj = ((previous_power_uw + current_power_uw) / 2) * dt_seconds / 1000
```

Use trapezoidal integration. `dt_seconds` comes from actual device `uptime_ms` differences, not an assumed `0.5` second constant. If uptime decreases, treat it as a device restart and reset the boot-session accumulator.

### OD680

```text
od680 = -log10((sample - dark) / (blank - dark))
```

Return `null` when required optical references are missing or physically invalid. Do not silently clamp invalid optical data into plausible OD values.

---

## Phase 1 REST/WS Surface

### REST

```text
GET /api/health
GET /api/system/status
GET /api/telemetry/latest?device_id=...&cell_id=...
GET /api/telemetry/history?device_id=...&cell_id=...&limit=...
```

`/api/health` is the lightweight process health check. Database and connected-device health/freshness are reported by `/api/system/status`.

### WebSocket

```text
/ws/device
/ws/dashboard
```

Every device implementation uses:

```text
X-BioVolt-Device-ID: <device-id>
Authorization: Bearer <shared-token>
```

There is no simulator-only device endpoint.

---

## Planned Commit Sequence

1. `chore: bootstrap FastAPI backend package`
2. `feat: add telemetry contract adapters and science core`
3. `feat: persist processed telemetry and cumulative energy`
4. `feat: add authenticated device websocket gateway`
5. `feat: add deterministic ESP32 simulator`
6. `test: add Phase 1 integration, Docker, CI and soak checks`
7. `test: enforce simulator to ESP32 substitution boundary`

Each commit must pass every test introduced up to that commit.

---

## Phase 1 Exit Criteria

- [ ] Phase 0 contract validation still passes unchanged.
- [ ] `GET /api/health` returns healthy backend process state.
- [ ] `GET /api/system/status` reports database state and connected-device freshness.
- [ ] Canonical raw Phase 0 example is accepted by the backend contract adapter.
- [ ] Malformed raw telemetry is rejected and is not persisted or broadcast.
- [ ] Device WebSocket rejects missing/wrong credentials.
- [ ] Authenticated simulator connects and normally transmits one frame every 500 ms.
- [ ] Backend computes current and power with unit-tested formulas.
- [ ] Backend computes OD680 only when valid optical references are configured.
- [ ] Cumulative energy uses actual device uptime and trapezoidal integration.
- [ ] Non-exact 500 ms frame intervals are processed correctly.
- [ ] Sequence gaps do not require fabricated samples or backend failure.
- [ ] Device restart resets boot-session energy state instead of integrating across invalid negative time.
- [ ] Live processed telemetry is broadcast at incoming cadence.
- [ ] SQLite stores approximately 1 sample/second/device/cell rather than every 500 ms frame.
- [ ] Raw payload is preserved for audit alongside queryable derived columns.
- [ ] `GET /api/telemetry/latest` returns latest processed data.
- [ ] `GET /api/telemetry/history` returns bounded chronological data.
- [ ] Sensor `null` values remain null and do not become fake zeroes.
- [ ] Simulator can intentionally emit sensor-null and malformed frames for rejection/fault tests.
- [ ] Backend + simulator start with Docker Compose.
- [ ] Backend also starts and remains functional with simulator stopped.
- [ ] Backend source and dependency metadata contain no `biovolt_simulator` dependency.
- [ ] Backend contains no simulator-device-ID conditional behavior.
- [ ] A generic hardware-like client that imports no simulator code successfully traverses `/ws/device -> processing -> persistence -> /ws/dashboard`.
- [ ] Smoke acceptance can target an arbitrary device ID.
- [ ] Replacing the simulator with the future ESP32 requires no FastAPI route, SQLite schema, scientific-calculation, processed-telemetry, or dashboard-interface change.
- [ ] Backend unit/integration tests and Phase 0 contract tests pass in GitHub Actions.
- [ ] A 30-minute simulator soak completes without backend crash and with expected persistence rate.

## Handoff to Phase 2 and Hardware Phase

Phase 2 builds the React/Vite/TypeScript PWA against the stable REST and `/ws/dashboard` interfaces.

The later real ESP32 phase must implement the already-proven device side of the boundary:

```text
ESP32 -> authenticated /ws/device -> device-telemetry.v1
```

It must not introduce a separate hardware-only backend protocol. Everything to the right of `/ws/device` stays unchanged.
