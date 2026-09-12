# Phase 1.4: Authenticated Device WebSocket and Dashboard Fanout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept authenticated raw telemetry on `/ws/device`, validate/process/persist it, broadcast processed telemetry to read-only dashboard clients on `/ws/dashboard`, and expose backend/device status plus latest/history REST endpoints.

**Architecture:** WebSocket responsibilities are split into small units: authentication, device registry, dashboard hub, and a telemetry service. Route handlers remain thin. The telemetry service owns the orchestration sequence `validate -> parse -> energy -> process -> optional persist -> broadcast` while domain calculations and repositories remain independently testable.

**Tech Stack:** FastAPI WebSocket, Pydantic, jsonschema, SQLAlchemy async repository, pytest, pytest-asyncio, Starlette/FastAPI TestClient or websockets-compatible test helpers.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- `/ws/device` requires both `X-BioVolt-Device-ID` and `Authorization: Bearer <token>`.
- Compare secrets using `secrets.compare_digest`.
- Device header ID must match raw payload `device_id`; mismatch is rejected.
- Invalid telemetry must not be persisted or broadcast.
- A malformed frame should not crash the application or disconnect unrelated clients.
- `/ws/dashboard` is read-only in Phase 1.
- Backend must preserve 500 ms live cadence and ~1 s persistence cadence.
- Server timestamp is UTC and timezone-aware.
- System status must be useful without a frontend.

---

### Task 1: Implement device authentication helper

**Files:**
- Create: `backend/src/biovolt_backend/websocket/__init__.py`
- Create: `backend/src/biovolt_backend/websocket/auth.py`
- Create: `backend/tests/websocket/test_auth.py`

**Interfaces:**
- Produces `authenticate_device(headers: Headers, expected_token: str) -> str` returning authenticated device ID.
- Raises a domain-specific `DeviceAuthenticationError` on missing/invalid credentials.

- [ ] **Step 1: Write failing valid-auth test**

```python
from starlette.datastructures import Headers
from biovolt_backend.websocket.auth import authenticate_device


def test_valid_device_auth_returns_device_id():
    headers = Headers({
        "x-biovolt-device-id": "biovolt-01",
        "authorization": "Bearer secret-12345",
    })
    assert authenticate_device(headers, "secret-12345") == "biovolt-01"
```

- [ ] **Step 2: Add rejection tests**

Cover:
- missing device ID
- missing Authorization
- wrong auth scheme
- wrong token
- blank device ID

- [ ] **Step 3: Implement helper with constant-time comparison**

```python
import secrets


def authenticate_device(headers: Headers, expected_token: str) -> str:
    device_id = headers.get("x-biovolt-device-id", "").strip()
    authorization = headers.get("authorization", "")
    if not device_id:
        raise DeviceAuthenticationError("missing device id")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise DeviceAuthenticationError("missing bearer token")
    supplied = authorization[len(prefix):]
    if not secrets.compare_digest(supplied, expected_token):
        raise DeviceAuthenticationError("invalid token")
    return device_id
```

- [ ] **Step 4: Run and commit**

```bash
pytest tests/websocket/test_auth.py -v
git add backend/src/biovolt_backend/websocket/auth.py backend/tests/websocket/test_auth.py
git commit -m "feat: authenticate BioVolt device websocket clients"
```

---

### Task 2: Implement connection registries

**Files:**
- Create: `backend/src/biovolt_backend/websocket/device_registry.py`
- Create: `backend/src/biovolt_backend/websocket/dashboard_hub.py`
- Create: `backend/tests/websocket/test_registries.py`

**Interfaces:**
- `DeviceRegistry.connect(device_id, websocket) -> None`
- `DeviceRegistry.disconnect(device_id, websocket) -> None`
- `DeviceRegistry.connected_device_ids() -> list[str]`
- `DeviceRegistry.mark_telemetry(device_id, received_at: datetime) -> None`
- `DeviceRegistry.latest_telemetry_at(device_id) -> datetime | None`
- `DashboardHub.connect(websocket) -> None`
- `DashboardHub.disconnect(websocket) -> None`
- `DashboardHub.broadcast_json(payload: dict) -> None`

- [ ] **Step 1: Write failing registry state tests**

Use lightweight fake websocket objects. Assert connection adds IDs, disconnect removes only the matching socket, and latest telemetry timestamp updates.

- [ ] **Step 2: Implement `DeviceRegistry` with async lock**

One device ID may reconnect. New socket should replace old registered socket only after the new route authenticates.

- [ ] **Step 3: Write dashboard broadcast failure test**

One fake dashboard socket raises during send; another succeeds. Broadcast must remove the failed socket and still deliver to the healthy socket.

- [ ] **Step 4: Implement `DashboardHub`**

Use a set of connections and isolate send failures per connection.

- [ ] **Step 5: Run and commit**

```bash
pytest tests/websocket/test_registries.py -v
git add backend/src/biovolt_backend/websocket/device_registry.py backend/src/biovolt_backend/websocket/dashboard_hub.py backend/tests/websocket/test_registries.py
git commit -m "feat: add device and dashboard connection registries"
```

---

### Task 3: Implement telemetry orchestration service

**Files:**
- Create: `backend/src/biovolt_backend/services/__init__.py`
- Create: `backend/src/biovolt_backend/services/telemetry_service.py`
- Create: `backend/tests/services/test_telemetry_service.py`

**Interfaces:**
- Produces `TelemetryService.handle_raw(payload: dict[str, object], authenticated_device_id: str, received_at: datetime) -> ProcessedTelemetryV1`.
- Constructor consumes:
  - `ProcessingConfig`
  - `EnergyAccumulator`
  - `PersistenceThrottle`
  - `TelemetryRepository`
  - `DashboardHub`
  - `DeviceRegistry`

- [ ] **Step 1: Write failing happy-path service test**

Use canonical raw payload and fakes for repository/hub/registry. Assert:
1. schema validated
2. authenticated ID equals payload ID
3. energy updated
4. processed telemetry returned
5. dashboard broadcast once
6. repository save occurs when throttle returns true
7. registry latest telemetry timestamp updated

- [ ] **Step 2: Write mismatched-device-ID test**

Authenticated header ID `biovolt-01` with payload `device_id=biovolt-02` must raise `TelemetryRejected` before persistence/broadcast.

- [ ] **Step 3: Write invalid-schema test**

Remove required `sequence`. Assert rejection and zero repository/hub calls.

- [ ] **Step 4: Implement orchestration**

Pseudo-order must be exactly:

```python
validate_payload("device-telemetry.v1.schema.json", payload)
raw = DeviceTelemetryV1.model_validate(payload)
if raw.device_id != authenticated_device_id:
    raise TelemetryRejected("device id mismatch")
energy_mj = energy.update(...)
processed = build_processed_telemetry(..., cumulative_energy_mj=energy_mj)
registry.mark_telemetry(raw.device_id, received_at)
if throttle.should_persist(raw.device_id, raw.cell_id, received_at):
    await repository.save(raw, processed, payload)
await dashboard_hub.broadcast_json(processed.model_dump(mode="json"))
return processed
```

- [ ] **Step 5: Run and commit**

```bash
pytest tests/services/test_telemetry_service.py -v
git add backend/src/biovolt_backend/services backend/tests/services/test_telemetry_service.py
git commit -m "feat: orchestrate telemetry validation processing and fanout"
```

---

### Task 4: Wire application lifespan dependencies

**Files:**
- Modify: `backend/src/biovolt_backend/main.py`
- Create: `backend/tests/test_lifespan.py`

**Interfaces:**
- App state must expose:
  - `settings`
  - `engine`
  - `session_factory`
  - `telemetry_repository`
  - `device_registry`
  - `dashboard_hub`
  - `telemetry_service`

- [ ] **Step 1: Write failing lifespan test**

Start app in test mode and assert required app-state services exist.

- [ ] **Step 2: Implement FastAPI lifespan context manager**

On startup:
- create engine/session factory
- initialize schema
- build repository, registry, hub, energy accumulator, throttle, processing config, telemetry service

On shutdown:
- dispose database engine

- [ ] **Step 3: Run and commit**

```bash
pytest tests/test_lifespan.py -v
git add backend/src/biovolt_backend/main.py backend/tests/test_lifespan.py
git commit -m "feat: initialize backend runtime services in app lifespan"
```

---

### Task 5: Add device and dashboard WebSocket routes

**Files:**
- Create: `backend/src/biovolt_backend/websocket/routes.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Create: `backend/tests/websocket/test_routes.py`

**Interfaces:**
- `WS /ws/device`
- `WS /ws/dashboard`

- [ ] **Step 1: Write failing unauthorized-device route test**

Connect without headers. Expected: WebSocket close code `1008` policy violation.

- [ ] **Step 2: Write authenticated-device telemetry test**

Connect with valid headers, send canonical raw payload, then assert repository/live state changes through test dependencies.

- [ ] **Step 3: Write dashboard receive test**

Connect dashboard socket, then send one valid device frame. Dashboard must receive processed payload with derived `current_ua`, `power_uw`, and server timestamp.

- [ ] **Step 4: Implement `/ws/device`**

Route behavior:
- authenticate before `accept()` when framework permits; otherwise accept then close immediately on auth failure
- register device
- receive text frames
- decode JSON
- call telemetry service
- on per-frame validation errors, send a compact error response to device and continue loop
- disconnect registry in `finally`

- [ ] **Step 5: Implement `/ws/dashboard`**

Accept, register, then keep connection alive by waiting for incoming frames/disconnect. Ignore any non-control client data in Phase 1; do not execute commands.

- [ ] **Step 6: Run route tests and commit**

```bash
pytest tests/websocket/test_routes.py -v
git add backend/src/biovolt_backend/websocket/routes.py backend/src/biovolt_backend/main.py backend/tests/websocket/test_routes.py
git commit -m "feat: add device and dashboard websocket routes"
```

---

### Task 6: Add system status and telemetry REST endpoints

**Files:**
- Create: `backend/src/biovolt_backend/api/status.py`
- Create: `backend/src/biovolt_backend/api/telemetry.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Create: `backend/tests/api/test_status.py`
- Create: `backend/tests/api/test_telemetry.py`

**Interfaces:**

`GET /api/system/status` returns at least:

```json
{
  "backend": "ok",
  "database": "ok",
  "connected_devices": ["biovolt-01"],
  "device_count": 1,
  "devices": {
    "biovolt-01": {
      "latest_telemetry_at": "2026-08-23T12:00:00Z",
      "latest_telemetry_age_ms": 250
    }
  }
}
```

`GET /api/telemetry/latest?device_id=biovolt-01&cell_id=cell-a`

`GET /api/telemetry/history?device_id=biovolt-01&cell_id=cell-a&limit=100`

- [ ] **Step 1: Write failing status test**

Inject registry state and verify exact counts/IDs.

- [ ] **Step 2: Write telemetry endpoint tests**

Verify:
- latest 404 when no data
- latest returns one processed row when present
- history default limit is bounded
- limit above configured maximum returns validation error or is explicitly capped, choose one behavior and document it

Recommended: `limit: int = Query(default=100, ge=1, le=1000)`.

- [ ] **Step 3: Implement routes using repository/registry from app state**

REST route code must not query SQLite directly outside repository methods.

- [ ] **Step 4: Run full module tests**

```bash
pytest tests/websocket tests/services tests/api -v
ruff check src tests
ruff format --check src tests
```

- [ ] **Step 5: Commit**

```bash
git add backend/src/biovolt_backend/api backend/src/biovolt_backend/main.py backend/tests/api
git commit -m "feat: expose BioVolt backend status and telemetry APIs"
```

## Module 1.4 Exit Criteria

- [ ] Device WebSocket authenticates shared token and device ID.
- [ ] Header/payload device mismatch is rejected.
- [ ] Invalid telemetry is neither persisted nor broadcast.
- [ ] Valid telemetry is processed, optionally persisted, and broadcast.
- [ ] One broken dashboard client does not prevent others receiving updates.
- [ ] Dashboard WebSocket is read-only.
- [ ] App lifespan initializes and disposes dependencies cleanly.
- [ ] System status exposes device connection and telemetry freshness.
- [ ] Latest/history REST endpoints use the repository abstraction.
- [ ] WebSocket/service/API tests and Ruff checks pass.
