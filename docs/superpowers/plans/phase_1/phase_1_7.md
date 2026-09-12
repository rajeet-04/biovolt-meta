# Phase 1.7: Simulator-to-Real-Hardware Substitution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Guarantee that the deterministic 500 ms simulator is a disposable development client that can later be replaced by the real ESP32 without changing FastAPI scientific processing, persistence, REST APIs, or dashboard fanout.

**Architecture:** FastAPI must be device-source neutral. Both the Python simulator and the future ESP32 are peers that implement the same Phase 0 `device-telemetry.v1` contract and connect through the same authenticated `/ws/device` endpoint. The backend must never import simulator code, inspect simulator-specific device IDs, depend on simulator timing behavior, or expose simulator-only endpoints. Real-hardware substitution is therefore an operational switch, not a backend rewrite.

**Tech Stack:** Phase 0 JSON Schema contracts, FastAPI WebSocket gateway, Python simulator, pytest, Docker Compose.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 1.1 through Phase 1.6.

## Global Constraints

- The simulator is test infrastructure only. It is not part of the production data model.
- The backend depends on `shared/schemas/` and backend domain models, never on `simulator/` Python modules.
- No backend source file may import `biovolt_simulator`.
- No backend decision may branch on device IDs such as `biovolt-sim-*`.
- The raw telemetry contract contains no `source_type`, `is_simulated`, or equivalent field solely to distinguish simulator from hardware.
- Simulator and real ESP32 use the same `WS /ws/device` endpoint.
- Simulator and real ESP32 use the same authentication headers:
  - `X-BioVolt-Device-ID: <device_id>`
  - `Authorization: Bearer <shared-token>`
- Simulator and real ESP32 send the same `device-telemetry.v1` JSON shape.
- The backend must not assume telemetry arrives at exactly 500 ms. The simulator defaults to 500 ms because that matches the planned ESP32 cadence, but processing must use each frame's `uptime_ms` and server receive time rather than hard-coded `0.5` second deltas.
- A real device may exhibit Wi-Fi jitter, delayed frames, or occasional lost frames without requiring backend changes.
- SQLite persistence throttling remains approximately 1 Hz independently of whether live telemetry comes from simulator or hardware.
- The simulator Compose service remains optional and must be stoppable while the backend continues running.

---

## Device Substitution Boundary

Both device implementations terminate at the same boundary:

```text
DEVELOPMENT

Deterministic Python simulator
          |
          | device-telemetry.v1
          | /ws/device
          v
       FastAPI
          |
          +--> scientific processing
          +--> SQLite
          +--> /ws/dashboard

REAL HARDWARE

ESP32 firmware
          |
          | device-telemetry.v1
          | /ws/device
          v
       FastAPI            <- unchanged
          |
          +--> scientific processing
          +--> SQLite
          +--> /ws/dashboard
```

The replacement operation later must be:

```text
1. Stop simulator client
2. Keep backend running
3. Configure ESP32 with laptop address, device ID, and shared token
4. ESP32 connects to the same /ws/device endpoint
5. ESP32 sends the same versioned raw telemetry contract
6. Existing backend processing continues without code modification
```

No database migration, endpoint change, processed-telemetry change, or frontend change is permitted merely because the source changed from simulator to ESP32.

---

### Task 1: Add backend dependency-boundary test

**Files:**
- Create: `backend/tests/architecture/test_device_source_neutrality.py`

**Interfaces:**
- Produces a test that proves backend source and dependency metadata do not depend on the simulator package.

- [ ] **Step 1: Write a failing architecture test before any accidental coupling exists**

The test should inspect backend Python files and `backend/pyproject.toml`.

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BACKEND_SRC = ROOT / "backend" / "src"


def test_backend_does_not_import_simulator_package():
    offenders = []
    for path in BACKEND_SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "biovolt_simulator" in text or "from simulator" in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == []
```

Also assert `backend/pyproject.toml` does not list `biovolt-simulator` as a dependency.

- [ ] **Step 2: Run the architecture test**

```bash
cd backend
pytest tests/architecture/test_device_source_neutrality.py -v
```

Expected: PASS once backend remains source neutral.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/architecture/test_device_source_neutrality.py
git commit -m "test: enforce device-source-neutral backend boundary"
```

---

### Task 2: Add cadence-independence tests

**Files:**
- Modify: `backend/tests/domain/test_energy.py`
- Modify: `backend/tests/services/test_telemetry_service.py`

**Interfaces:**
- Existing energy accumulator consumes actual `uptime_ms` differences.
- Backend processing accepts valid frames regardless of exact inter-frame interval.

- [ ] **Step 1: Add non-500-ms energy test**

Send powers at device uptimes such as:

```text
1000 ms
1575 ms
2110 ms
```

Assert trapezoidal integration uses `575 ms` and `535 ms`, not hard-coded `500 ms`.

- [ ] **Step 2: Add delayed-frame service test**

Process two valid frames whose server receive timestamps differ substantially from device uptime intervals. Assert energy follows device uptime and telemetry remains accepted.

- [ ] **Step 3: Add lost-sequence test**

Process sequence `100`, then `102`. The second frame remains valid if its schema and uptime are valid. The backend may later record the sequence gap diagnostically, but it must not fabricate the missing sample or require simulator-perfect sequencing.

- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/domain/test_energy.py tests/services/test_telemetry_service.py -v
git add tests/domain/test_energy.py tests/services/test_telemetry_service.py
git commit -m "test: prove telemetry processing is cadence independent"
```

---

### Task 3: Add generic hardware-like WebSocket parity test

**Files:**
- Create: `backend/tests/integration/test_device_source_parity.py`

**Interfaces:**
- Test client is implemented inside the backend integration test and does not import simulator code.
- Sends a valid Phase 0 payload with a hardware-style ID such as `biovolt-hw-test-01`.

- [ ] **Step 1: Connect a generic device client**

Use the same route and auth headers as the simulator:

```text
X-BioVolt-Device-ID: biovolt-hw-test-01
Authorization: Bearer <test-token>
```

- [ ] **Step 2: Send raw telemetry directly from the canonical contract fixture**

Change only identity/sequence/uptime/measurement values required by the test. Do not use `TelemetryGenerator` or any simulator helper.

- [ ] **Step 3: Assert complete parity**

The generic client must produce the same downstream behavior as the simulator:

1. frame validates
2. current is derived
3. power is derived
4. valid OD680 is derived when optical references are configured
5. cumulative energy updates
6. persistence occurs according to throttle
7. dashboard receives processed telemetry
8. `/api/system/status` lists `biovolt-hw-test-01`
9. `/api/telemetry/latest` returns its data

- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/integration/test_device_source_parity.py -v
git add tests/integration/test_device_source_parity.py
git commit -m "test: verify simulator and hardware device contract parity"
```

---

### Task 4: Document explicit simulator-to-hardware switchover

**Files:**
- Modify: `README.md`
- Modify: `simulator/README.md`
- Modify: `backend/README.md`

**Interfaces:**
- Development simulator run:

```bash
docker compose --profile simulator up -d
```

- Real-hardware backend-only run:

```bash
docker compose stop simulator
docker compose up -d backend
```

The later ESP32 configuration should target:

```text
ws://<laptop-hotspot-ip>:8000/ws/device
```

with a unique real device ID and the configured shared token.

- [ ] **Step 1: Document that the simulator is optional disposable infrastructure**

State explicitly that it exists to unblock backend/frontend work before hardware is ready.

- [ ] **Step 2: Document replacement procedure**

```text
Simulator ON  -> backend tested without hardware
Simulator OFF -> backend remains running
ESP32 ON      -> same backend accepts real measurements
```

- [ ] **Step 3: Document non-goals**

Do not require:
- simulator package on the laptop when running real hardware
- simulator container in the final demo
- backend feature flags to select simulated vs real telemetry
- a different database table for real telemetry

- [ ] **Step 4: Commit**

```bash
git add README.md backend/README.md simulator/README.md
git commit -m "docs: define simulator to ESP32 switchover procedure"
```

---

### Task 5: Add substitution acceptance gate

**Files:**
- Modify: `scripts/phase1_smoke.py`
- Modify: `docs/superpowers/plans/phase_1/phase_1_6.md` only if acceptance implementation requires command documentation changes

**Interfaces:**
- Smoke script accepts expected device ID rather than hard-coding `biovolt-sim-01`.

Recommended CLI:

```bash
python scripts/phase1_smoke.py --device-id biovolt-sim-01
```

Later hardware test:

```bash
python scripts/phase1_smoke.py --device-id biovolt-01
```

- [ ] **Step 1: Remove simulator-specific device ID from smoke-test logic**

The default may remain `biovolt-sim-01` for Phase 1 convenience, but a CLI option must override it.

- [ ] **Step 2: Verify simulator mode**

```bash
docker compose --profile simulator up -d
python scripts/phase1_smoke.py --device-id biovolt-sim-01
```

Expected: PASS.

- [ ] **Step 3: Verify generic device mode in automated integration tests**

Run:

```bash
cd backend
pytest tests/integration/test_device_source_parity.py -v
```

Expected: PASS without importing or starting the simulator package.

- [ ] **Step 4: Preserve the command for later ESP32 hardware acceptance**

When Phase 3 introduces real firmware, the hardware gate becomes:

```bash
docker compose stop simulator
docker compose up -d backend
python scripts/phase1_smoke.py --device-id biovolt-01
```

with the real ESP32 connected separately to `/ws/device`.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase1_smoke.py
git commit -m "test: make Phase 1 smoke checks device-source neutral"
```

---

## Phase 1.7 Exit Criteria

- [ ] Backend contains no dependency on `biovolt_simulator`.
- [ ] Backend contains no simulator-ID conditional logic.
- [ ] Simulator-specific metadata is not added to the shared raw telemetry schema.
- [ ] Backend processes non-exact 500 ms telemetry intervals correctly.
- [ ] Sequence gaps do not require backend rewrites or fabricated samples.
- [ ] A generic non-simulator WebSocket client passes the same processing/persistence/fanout path.
- [ ] Simulator service can be stopped without stopping or rebuilding FastAPI.
- [ ] Smoke acceptance can target an arbitrary device ID.
- [ ] Documentation contains the exact future simulator-to-ESP32 switchover procedure.
- [ ] Replacing the simulator with the real ESP32 requires no FastAPI route, database schema, scientific calculation, or dashboard-contract changes.

## Handoff to Real ESP32 Phase

When the real ESP32 firmware is implemented, it must consume the existing Phase 0 raw telemetry schema instead of inventing a second hardware protocol. The hardware phase should implement serialization and authentication to the interface proven by this plan.

The intended transition is:

```text
Phase 1
Simulator -> /ws/device -> FastAPI

Hardware phase
ESP32     -> /ws/device -> FastAPI
```

Everything to the right of `/ws/device` remains unchanged.
