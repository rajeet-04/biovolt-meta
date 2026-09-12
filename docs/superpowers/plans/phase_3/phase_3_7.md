# Phase 3.7: Real-Hardware Backend/PWA Parity and Telemetry-Gap Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the simulator can be switched off and the real ESP32 can take its place without backend/frontend rewrites, while preventing cumulative-energy inflation across dropped telemetry intervals.

**Architecture:** Hardware parity is verified through the exact same `/ws/device -> FastAPI -> SQLite -> /ws/dashboard -> PWA` path already exercised by the simulator. A source-neutral backend continuity tracker treats a telemetry sequence gap as an observation discontinuity: accumulated energy is preserved, but the unobserved interval is not numerically integrated.

**Tech Stack:** Existing FastAPI backend, pytest, ESP32 firmware, Phase 2 PWA, Docker Compose.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Do not create hardware-only API endpoints or hardware/source discriminator fields.
- Real ESP32 and simulator use the same raw schema and authentication path.
- Missing telemetry is unknown data. Do not interpolate or integrate across an unobserved interval.
- Cumulative energy before a sequence gap is preserved.
- First frame after a gap establishes a new energy anchor and contributes zero energy for the missing interval.
- A true device reboot, detected by decreasing uptime, still resets boot-session energy to zero according to Phase 1 semantics.
- Processed telemetry v1 contains `control.mode` but does **not** contain `optimizer_direction`. `optimizer_direction=0` is verified in raw device telemetry, not invented by the PWA.
- `uint32_t` sequence wraparound handling is outside Phase 3 because at 2 Hz wraparound is decades away; document the assumption explicitly.

---

### Task 1: Add source-neutral telemetry continuity tracker

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
duplicate/older sequence           contiguous=False, restarted=False
uptime decreases                   contiguous=False, restarted=True
```

- [ ] **Step 1: Write failing tests**

Cover contiguous `100 -> 101`, gap `100 -> 103`, duplicate `100 -> 100`, older `100 -> 99`, and reboot `uptime 5000 -> 100`.

- [ ] **Step 2: Implement tracker keyed by `(device_id, cell_id)`**

Keep only last accepted sequence/uptime per source. Source identity is generic and contains no simulator/hardware branch.

- [ ] **Step 3: Run and commit**

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
- replace last uptime/power anchor with supplied frame,
- add no energy for the interval leading to the supplied frame.

- [ ] **Step 1: Write failing gap-anchor test**

```python
acc = EnergyAccumulator()
acc.update("d1", "c1", 0, 10.0)
assert acc.update("d1", "c1", 1000, 10.0) == pytest.approx(0.010)
assert acc.anchor("d1", "c1", 10000, 20.0) == pytest.approx(0.010)
assert acc.update("d1", "c1", 11000, 20.0) == pytest.approx(0.030)
```

The 9-second unobserved interval contributes zero.

- [ ] **Step 2: Preserve reboot test**

Existing uptime-decrease behavior remains reset-to-zero.

- [ ] **Step 3: Implement anchor without duplicating integration formula**

- [ ] **Step 4: Run and commit**

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
- `TelemetryService` constructor receives one `TelemetryContinuityTracker`.

Processing order:

```text
validate raw schema
parse raw model
authenticated device-ID check
continuity.observe(sequence, uptime)
if restarted:
    energy.reset(source)
    energy.anchor(current frame)
elif contiguous:
    energy.update(current frame)
else:
    energy.anchor(current frame)
build processed telemetry
persist according to throttle
broadcast
```

- [ ] **Step 1: Write failing gap service test**

Feed sequence 10 at uptime 1000, sequence 11 at 1500, then sequence 20 at 10000. Sequence 20 cumulative energy must equal the cumulative total from sequence 11.

- [ ] **Step 2: Write resumed-contiguous test**

Sequence 21 at 10500 integrates only the 500 ms interval from sequence 20 to 21.

- [ ] **Step 3: Write reboot service test**

A lower uptime causes boot-session cumulative energy reset while retaining valid processing of the new frame as anchor.

- [ ] **Step 4: Wire one tracker in app lifespan**

- [ ] **Step 5: Run and commit**

```bash
pytest tests/services tests/integration -v
git add src/biovolt_backend/services/telemetry_service.py src/biovolt_backend/main.py tests/services/test_telemetry_service.py
git commit -m "fix: treat BioVolt telemetry gaps as energy discontinuities"
```

---

### Task 4: Add real ESP32 parity checklist

**Files:**
- Create: `scripts/phase3_hardware_parity.md`

- [ ] **Step 1: Start backend/PWA with simulator disabled**

```bash
docker compose stop simulator || true
docker compose --profile frontend up --build -d
```

- [ ] **Step 2: Provision actual laptop network details and reboot ESP32**

Set:

```text
laptop hotspot SSID/password
actual laptop hotspot/backend IP
backend port 8000
device_id biovolt-01
cell_id cell-a
shared token matching backend
```

- [ ] **Step 3: Verify backend identity**

```bash
curl http://localhost:8000/api/system/status
```

Expected configured real device ID is connected.

- [ ] **Step 4: Verify latest processed telemetry**

```bash
curl "http://localhost:8000/api/telemetry/latest?device_id=biovolt-01&cell_id=cell-a"
```

Verify exactly:

```text
processed sequence increases
voltage reflects physical ADS1115 channel A0
current/power are backend-derived
OD680 is present only when backend optical references are valid
control.mode == "monitor"
processed telemetry contains no optimizer_direction field
```

- [ ] **Step 5: Verify raw Phase 3 optimizer state separately**

Use firmware native serializer test or a safe debug capture of one raw device frame and verify:

```json
"control": {
  "mode": "monitor",
  "optimizer_direction": 0
}
```

Do not add optimizer_direction to processed telemetry/PWA merely for this check.

- [ ] **Step 6: Verify PWA without rebuild**

Existing PWA metric components must render the real device with no `Hardware`/`Simulator` branch inferred from the device ID.

- [ ] **Step 7: Commit checklist**

```bash
git add scripts/phase3_hardware_parity.md
git commit -m "docs: add real ESP32 parity acceptance checklist"
```

---

### Task 5: Verify backend-outage gap behavior with physical device

**Files:**
- Modify: `scripts/phase3_hardware_parity.md`

- [ ] **Step 1: Record current sequence, uptime, and cumulative energy**

- [ ] **Step 2: Stop backend for 15 seconds while ESP32 remains powered**

```bash
docker compose stop backend
sleep 15
docker compose start backend
```

- [ ] **Step 3: Confirm reconnect without ESP32 reboot**

Uptime continues increasing and first received sequence jumps because unsent scheduled frames were discarded.

- [ ] **Step 4: Confirm first post-gap energy does not jump**

First post-reconnect processed frame preserves pre-gap cumulative total. The next contiguous frame resumes normal integration.

- [ ] **Step 5: Verify PWA reconnect/resync**

PWA moves through stale/disconnected and returns to live without a source-specific reload.

- [ ] **Step 6: Record evidence**

```text
pre-gap sequence
post-gap sequence
ESP32 uptime before/after
pre-gap cumulative mJ
first post-gap cumulative mJ
second post-gap cumulative mJ
```

## Module 3.7 Exit Criteria

- [ ] Continuity logic is source-neutral.
- [ ] Sequence gaps/duplicates are treated as observation discontinuities.
- [ ] Energy is never integrated across an unobserved gap.
- [ ] Device reboot still resets boot-session energy.
- [ ] Real ESP32 replaces simulator without backend route/schema changes.
- [ ] Processed telemetry remains contract-exact and does not gain optimizer_direction.
- [ ] PWA renders real device without rebuild or simulator/hardware-specific logic.
- [ ] Backend restart/outage does not require ESP32 reboot.
