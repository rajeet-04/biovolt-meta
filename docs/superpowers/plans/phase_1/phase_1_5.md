# Phase 1.5: Deterministic ESP32 Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic Python simulator that emits valid Phase 0 raw device telemetry every 500 ms, authenticates to the Phase 1 device WebSocket, reconnects after interruption, and can intentionally exercise sensor-null and malformed-payload behavior.

**Architecture:** The simulator is a separate Python package. `generator.py` owns deterministic synthetic biology/electrical state and emits plain dictionaries matching `device-telemetry.v1`. `client.py` owns WebSocket transport/reconnect. The CLI combines them but keeps generation testable without a running backend.

**Tech Stack:** Python 3.11+, websockets, Pydantic Settings, jsonschema, pytest, pytest-asyncio.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Simulator payloads must validate against the merged Phase 0 raw telemetry schema.
- Default cadence is exactly 0.5 seconds between generated frames.
- Sequence increments by 1 per emitted frame.
- Uptime increases monotonically from simulator boot and resets only when the simulator process restarts.
- Synthetic optical values must be physically coherent with OD: increasing OD means decreasing BPW34 transmitted-light reading.
- Simulator must never put derived `current_ua`, `power_uw`, `od680`, biomass, carbon, or cumulative energy into raw telemetry.
- Fault modes must be explicit CLI/config choices and deterministic under a fixed seed.

---

### Task 1: Bootstrap simulator package and settings

**Files:**
- Create: `simulator/pyproject.toml`
- Create: `simulator/src/biovolt_simulator/__init__.py`
- Create: `simulator/src/biovolt_simulator/config.py`
- Create: `simulator/tests/test_config.py`
- Modify: `simulator/README.md`

**Interfaces:**
- Produces `SimulatorSettings` with:
  - `backend_ws_url: str`
  - `device_id: str = "biovolt-sim-01"`
  - `cell_id: str = "cell-a"`
  - `device_token: str`
  - `interval_seconds: float = 0.5`
  - `seed: int = 42`
  - `start_sequence: int = 1`

- [ ] **Step 1: Write failing settings test**

```python
from biovolt_simulator.config import SimulatorSettings


def test_default_interval_is_500_ms():
    settings = SimulatorSettings(
        backend_ws_url="ws://localhost:8000/ws/device",
        device_token="test-token-123",
    )
    assert settings.interval_seconds == 0.5
```

- [ ] **Step 2: Create simulator `pyproject.toml`**

```toml
[project]
name = "biovolt-simulator"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "websockets>=15,<16",
  "pydantic>=2.11,<3",
  "pydantic-settings>=2.10,<3",
  "jsonschema>=4.25,<5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.4,<9",
  "pytest-asyncio>=1.1,<2",
  "ruff>=0.12,<1",
]

[project.scripts]
biovolt-simulator = "biovolt_simulator.__main__:main"
```

- [ ] **Step 3: Implement `SimulatorSettings` with `BIOVOLT_SIM_` env prefix**

Reject `interval_seconds <= 0` and blank token/device IDs.

- [ ] **Step 4: Install and run tests**

```bash
cd simulator
python -m pip install -e '.[dev]'
pytest -v
```

- [ ] **Step 5: Commit**

```bash
git add simulator
git commit -m "chore: bootstrap BioVolt ESP32 simulator package"
```

---

### Task 2: Implement deterministic telemetry generator

**Files:**
- Create: `simulator/src/biovolt_simulator/generator.py`
- Create: `simulator/tests/test_generator.py`

**Interfaces:**
- Produces `SimulatorState`.
- Produces `TelemetryGenerator.next_frame(elapsed_seconds: float) -> dict[str, object]`.

Recommended deterministic model:

```text
OD target(t) = start_od + growth_rate_per_second * t
BPW34 sample = dark + (blank - dark) * 10^(-OD target) + seeded noise
Voltage = base_voltage_mv + slow sine + seeded low-amplitude noise
Temperature = 26.0 + 0.3 * sin(t / 60)
Lux = base_lux + pwm-dependent contribution + seeded noise
```

This is not claimed as a biological simulator. It is a protocol/integration signal generator with internally coherent optical behavior.

- [ ] **Step 1: Write failing determinism test**

```python
def test_same_seed_produces_same_first_frames():
    a = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")
    b = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")
    assert a.next_frame(0.0) == b.next_frame(0.0)
    assert a.next_frame(0.5) == b.next_frame(0.5)
```

- [ ] **Step 2: Write sequence/uptime test**

Two calls at elapsed `0.0` and `0.5` must increment sequence by one and uptime by about 500 ms.

- [ ] **Step 3: Write optical-coherence test**

Generate frames at `t=0` and a later time with positive growth rate. Assert later `bpw34_raw` is lower than early reading when noise is disabled in the test constructor.

- [ ] **Step 4: Implement generator**

Make noise amplitudes constructor parameters so tests can set them to zero. Generated payload must include exact Phase 0 nested sections and health flags.

- [ ] **Step 5: Validate every generated test frame against Phase 0 schema**

Reuse a simulator-side helper that loads `../shared/schemas/device-telemetry.v1.schema.json`, or add repository root as an explicit generator test fixture. Do not duplicate the schema.

- [ ] **Step 6: Run and commit**

```bash
pytest tests/test_generator.py -v
git add simulator/src/biovolt_simulator/generator.py simulator/tests/test_generator.py
git commit -m "feat: generate deterministic BioVolt raw telemetry"
```

---

### Task 3: Add explicit sensor-null fault modes

**Files:**
- Modify: `simulator/src/biovolt_simulator/generator.py`
- Create: `simulator/src/biovolt_simulator/faults.py`
- Create: `simulator/tests/test_faults.py`

**Interfaces:**
- Produces fault options such as:
  - `temperature_null`
  - `light_null`
  - `bpv_voltage_null`
  - `bpw34_null`
- When a measurement becomes null, its corresponding health flag becomes false.

- [ ] **Step 1: Write failing temperature-fault test**

Assert `environment.temperature_c is None` and `health.temperature_ok is False` while the resulting frame still validates against Phase 0 schema.

- [ ] **Step 2: Implement fault transformer**

Use a pure function:

```python
def apply_fault(payload: dict[str, object], fault: str) -> dict[str, object]:
    ...
```

Deep-copy input so the base generator state is not corrupted.

- [ ] **Step 3: Add one test per supported sensor-null fault**

- [ ] **Step 4: Run and commit**

```bash
pytest tests/test_faults.py -v
git add simulator/src/biovolt_simulator/faults.py simulator/src/biovolt_simulator/generator.py simulator/tests/test_faults.py
git commit -m "feat: simulate BioVolt sensor failure states"
```

---

### Task 4: Implement authenticated WebSocket client with reconnect

**Files:**
- Create: `simulator/src/biovolt_simulator/client.py`
- Create: `simulator/tests/test_client.py`

**Interfaces:**
- Produces `SimulatorClient.run() -> None`.
- Sends headers:

```text
X-BioVolt-Device-ID: <device_id>
Authorization: Bearer <device_token>
```

- [ ] **Step 1: Write failing header-construction test**

Extract a pure helper `device_headers(settings) -> dict[str, str]` and assert exact values.

- [ ] **Step 2: Write reconnect-backoff unit test**

Backoff sequence should be bounded, for example `1, 2, 4, 8, 10, 10...` seconds. Expose `reconnect_delay(attempt: int) -> float` as a pure function.

- [ ] **Step 3: Implement async send loop**

Pseudo-structure:

```python
while True:
    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            attempt = 0
            started = monotonic()
            while True:
                elapsed = monotonic() - started
                frame = generator.next_frame(elapsed)
                await ws.send(json.dumps(frame))
                await asyncio.sleep(interval_seconds)
    except (OSError, websockets.WebSocketException):
        await asyncio.sleep(reconnect_delay(attempt))
        attempt += 1
```

- [ ] **Step 4: Ensure cancellation propagates**

Do not swallow `asyncio.CancelledError`.

- [ ] **Step 5: Run and commit**

```bash
pytest tests/test_client.py -v
git add simulator/src/biovolt_simulator/client.py simulator/tests/test_client.py
git commit -m "feat: connect simulator to BioVolt device websocket"
```

---

### Task 5: Add CLI and malformed-frame mode

**Files:**
- Create: `simulator/src/biovolt_simulator/__main__.py`
- Create: `simulator/tests/test_cli.py`

**Interfaces:**
- CLI flags:

```text
--backend-ws-url
--device-id
--cell-id
--token
--interval
--seed
--fault <name>
--malformed-every <N>
```

`--malformed-every 0` means disabled.

- [ ] **Step 1: Write CLI parser test**

Verify flags override environment/defaults.

- [ ] **Step 2: Define malformed packet behavior**

Every Nth frame, remove a required field such as `sequence`. This mode intentionally violates the schema and is only for backend rejection testing.

- [ ] **Step 3: Implement CLI entrypoint**

The CLI prints on startup:

```text
BioVolt simulator
Device: biovolt-sim-01
Cell: cell-a
Target: ws://localhost:8000/ws/device
Cadence: 0.5 s
Seed: 42
```

Never print the token.

- [ ] **Step 4: Run simulator quality gates**

```bash
pytest -v
ruff check src tests
ruff format --check src tests
```

- [ ] **Step 5: Update README and commit**

Document normal run, one sensor-fault run, and malformed-frame run.

```bash
git add simulator
git commit -m "feat: expose BioVolt simulator CLI and fault modes"
```

## Module 1.5 Exit Criteria

- [ ] Simulator package installs and runs independently.
- [ ] Default frames are deterministic under seed 42.
- [ ] Default frame cadence is 500 ms.
- [ ] Raw payloads validate against Phase 0 schema.
- [ ] OD-like synthetic growth causes lower transmitted BPW34 values over time.
- [ ] Simulator emits no backend-derived fields.
- [ ] Sensor-null fault modes update both value and health flag.
- [ ] Client sends approved device-auth headers and reconnects with bounded backoff.
- [ ] Malformed mode can intentionally violate the contract for rejection tests.
- [ ] Token is never printed in logs.
- [ ] Simulator tests and Ruff checks pass.
