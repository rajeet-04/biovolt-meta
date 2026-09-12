# Phase 3.7: Real-Hardware Backend/PWA Parity and Telemetry-Gap Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the simulator can be switched off and the real ESP32 can take its place without backend/frontend rewrites, while preventing cumulative-energy inflation across dropped telemetry intervals.

**Architecture:** Hardware parity is verified through the exact same `/ws/device -> FastAPI -> SQLite -> /ws/dashboard -> PWA` path already tested by the simulator. A source-neutral backend continuity tracker treats a telemetry sequence gap as an observation discontinuity: cumulative energy is preserved, but the unobserved interval is not numerically integrated.

**Tech Stack:** Existing FastAPI backend, pytest, ESP32 firmware, Phase 2 PWA, Docker Compose.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Do not create hardware-only API endpoints.
- Do not add `is_hardware`, `is_simulated`, `source_type`, or equivalent fields.
- Real ESP32 and simulator continue using the same raw schema and auth route.
- A missing telemetry interval is unknown data. Do not interpolate energy across it as if measurements existed.
- Cumulative energy before a sequence gap is preserved.
- First frame after a sequence gap establishes a new integration anchor and adds zero energy for the missing interval.
- A true device reboot, detected by decreasing uptime, still resets boot-session energy to zero according to Phase 1 semantics.
- Sequence wraparound is not required in Phase 3 because `uint32_t` at 2 Hz has multi-decade lifetime; document this explicitly.

---

### Task 1: Add source-neutral telemetry continuity tracker to backend

**Files:**
- Create: `backend/src/biovolt_backend/domain/continuity.py`
- Create: `backend/tests/domain/test_continuity.py`

**Interfaces:**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuityResult:
    contiguous: bool
    restarted: bool


class TelemetryContinuityTracker:
    def observe(
        self,
        device_id: str,
        cell_id: str,
        sequence: int,
        uptime_ms: int,
    ) -> ContinuityResult: ...

    def reset(self, device_id: str, cell_id: str) -> None: ...
```

Rules:

```text
first frame                        contiguous=False, restarted=False
sequence previous+1, uptime up     contiguous=True,  restarted=False
sequence gap, uptime up            contiguous=False, restarted=False
same/older sequence, uptime up     contiguous=False, restarted=False
uptime decreases                   contiguous=False, restarted=True
```

- [ ] **Step 1: Write failing continuity tests**

Cover exact contiguous frames `100 -> 101`, gap `100 -> 103`, duplicate `100 -> 100`, and reboot `uptime 5000 -> 100`.

- [ ] **Step 2: Implement tracker keyed by `(device_id, cell_id)`**

Store only last sequence/uptime for each source.

- [ ] **Step 3: Run tests and commit**

```bash
cd backend
pytest tests/domain/test_continuity.py -v
git add src/biovolt_backend/domain/continuity.py tests/domain/test_continuity.py
git commit -m "feat: track BioVolt telemetry continuity"
```

---

### Task 2: Add non-integrating energy anchor operation

**Files:**
- Modify: `backend/src/biovolt_backend/domain/energy.py`
- Modify: `backend/tests/domain/test_energy.py`

**Interfaces:**

Add:

```python
EnergyAccumulator.anchor(
    device_id: str,
    cell_id: str,
    uptime_ms: int,
    power_uw: float | None,
) -> float
```

Behavior:
- preserve current cumulative mJ,
- replace stored last uptime/power with the supplied frame,
- add no energy for the interval leading to the supplied frame.

- [ ] **Step 1: Write failing gap-anchor test**

Example:

```python
acc = EnergyAccumulator()
acc.update("d1", "c1", 0, 10.0)
assert acc.update("d1", "c1", 1000, 10.0) == pytest.approx(0.010)
assert acc.anchor("d1", "c1", 10000, 20.0) == pytest.approx(0.010)
assert acc.update("d1", "c1", 11000, 20.0) == pytest.approx(0.030)
```

The 9-second unobserved interval contributes zero.

- [ ] **Step 2: Preserve reboot behavior**

Existing uptime-decrease test remains reset-to-zero.

- [ ] **Step 3: Implement `anchor()`**

Do not duplicate integration formulas.

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/domain/test_energy.py -v
git add src/biovolt_backend/domain/energy.py tests/domain/test_energy.py
git commit -m "feat: prevent energy integration across telemetry gaps"
```

---

### Task 3: Integrate continuity into TelemetryService

**Files:**
- Modify: `backend/src/biovolt_backend/services/telemetry_service.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Modify: `backend/tests/services/test_telemetry_service.py`

**Interfaces:**
- `TelemetryService` constructor receives `TelemetryContinuityTracker`.

Processing order becomes:

```text
validate raw schema
parse raw model
authenticated device ID check
continuity.observe(sequence, uptime)
if restarted:
    energy.reset(...)
    energy.anchor(current frame)
elif contiguous:
    energy.update(current frame)
else:
    energy.anchor(current frame)
build processed telemetry
persist when throttle allows
broadcast
```

- [ ] **Step 1: Write failing sequence-gap service test**

Feed valid sequence `10` at uptime `1000`, sequence `11` at `1500`, then sequence `20` at `10000`. Assert cumulative energy at sequence 20 equals cumulative value at sequence 11, not a large bridged value.

- [ ] **Step 2: Write next-contiguous-frame test**

Sequence `21` at `10500` resumes normal trapezoidal integration from sequence 20.

- [ ] **Step 3: Wire tracker into application lifespan**

One tracker instance per FastAPI process.

- [ ] **Step 4: Run service/integration tests and commit**

```bash
pytest tests/services tests/integration -v
git add src/biovolt_backend/services/telemetry_service.py src/biovolt_backend/main.py tests/services/test_telemetry_service.py
git commit -m "fix: treat BioVolt telemetry gaps as energy discontinuities"
```

---

### Task 4: Add real ESP32 parity integration checklist

**Files:**
- Create: `scripts/phase3_hardware_parity.md`

- [ ] **Step 1: Start backend and PWA with simulator disabled**

```bash
docker compose stop simulator || true
docker compose --profile frontend up --build -d
```

- [ ] **Step 2: Connect laptop hotspot and ESP32**

Provision ESP32 with:

```text
SSID/password of laptop hotspot
backend_host = laptop hotspot gateway/IP
backend_port = 8000
device_id = biovolt-01
cell_id = cell-a
shared token matching backend
```

- [ ] **Step 3: Verify backend identity**

```bash
curl http://localhost:8000/api/system/status
```

Expected: `biovolt-01` connected.

- [ ] **Step 4: Verify latest telemetry**

```bash
curl "http://localhost:8000/api/telemetry/latest?device_id=biovolt-01&cell_id=cell-a"
```

Verify:

```text
real sequence increases
voltage reflects physical ADC
current/power are backend-derived
OD680 appears only when backend optical calibration is valid
control.mode=monitor
optimizer_direction is not exposed in processed payload unless contract includes it
```

- [ ] **Step 5: Verify PWA without rebuild**

Open existing PWA. It must render the real device using the same metric components used for simulator data and must not add a hardware-specific branch.

- [ ] **Step 6: Commit checklist**

```bash
git add scripts/phase3_hardware_parity.md
git commit -m "docs: add real ESP32 parity acceptance checklist"
```

---

### Task 5: Verify reconnect gap behavior with physical device

**Files:**
- Modify: `scripts/phase3_hardware_parity.md`

- [ ] **Step 1: Record current sequence and cumulative energy**

- [ ] **Step 2: Stop backend for 15 seconds while ESP32 stays powered**

```bash
docker compose stop backend
sleep 15
docker compose start backend
```

- [ ] **Step 3: Confirm ESP32 reconnects without reboot**

Uptime remains increasing. Received sequence jumps because frames were discarded during outage.

- [ ] **Step 4: Confirm cumulative energy does not jump across the missing interval**

First post-reconnect frame preserves the pre-gap accumulated total. Following contiguous frame resumes integration.

- [ ] **Step 5: Verify PWA reconnect/resync behavior**

PWA transitions through stale/disconnected and returns to live without a source-specific refresh.

- [ ] **Step 6: Commit documented result format**

Record in PR notes:

```text
pre-gap sequence
post-gap sequence
pre-gap cumulative mJ
first post-gap cumulative mJ
second post-gap cumulative mJ
ESP32 uptime before/after
```

## Module 3.7 Exit Criteria

- [ ] Backend remains source-neutral.
- [ ] Sequence gaps are detected independently of simulator/hardware identity.
- [ ] Energy is not integrated across unobserved telemetry intervals.
- [ ] Device reboot still resets boot-session energy.
- [ ] Real ESP32 replaces simulator without backend route/schema changes.
- [ ] Existing PWA renders real device without rebuild or simulator-specific logic.
- [ ] Backend restart/outage does not require ESP32 reboot.
