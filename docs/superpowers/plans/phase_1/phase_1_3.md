# Phase 1.3: SQLite Persistence and Energy Accumulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist processed telemetry to SQLite at approximately 1 Hz per device/cell while preserving raw payloads for audit and calculating boot-session cumulative electrical energy from every 500 ms frame.

**Architecture:** SQLAlchemy 2.x async ORM stores telemetry in SQLite. The energy accumulator is pure in-memory state keyed by `(device_id, cell_id)` and uses device uptime for trapezoidal integration. A persistence throttle independently decides whether the current processed frame should be written, so live processing remains 2 Hz while disk writes remain about 1 Hz.

**Tech Stack:** SQLAlchemy 2.x async ORM, aiosqlite, Pydantic v2, pytest, pytest-asyncio.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Every incoming valid frame may affect cumulative energy even when it is not persisted.
- Persistence cadence is independent of live broadcast cadence.
- Raw payload JSON must be preserved exactly enough for post-hoc audit.
- `null` sensor fields remain database `NULL`.
- Device uptime is the primary energy integration timebase.
- If uptime decreases, treat the device as restarted and reset boot-session energy state.
- Duplicate or non-increasing uptime must not add energy.
- Phase 1 database schema may include `experiment_id` only as nullable text without implementing experiment lifecycle.

---

### Task 1: Add async database engine and test fixtures

**Files:**
- Create: `backend/src/biovolt_backend/persistence/__init__.py`
- Create: `backend/src/biovolt_backend/persistence/database.py`
- Create: `backend/tests/persistence/test_database.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Produces `create_engine_and_session(database_url: str)` returning async engine and session factory.
- Produces `init_database(engine) -> None`.

- [ ] **Step 1: Write failing database initialization test**

```python
import pytest
from sqlalchemy import text

from biovolt_backend.persistence.database import create_engine_and_session, init_database


@pytest.mark.asyncio
async def test_database_connection_is_usable(tmp_path):
    url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = create_engine_and_session(url)
    await init_database(engine)
    async with session_factory() as session:
        value = await session.scalar(text("SELECT 1"))
    assert value == 1
    await engine.dispose()
```

- [ ] **Step 2: Run and verify failure**

```bash
pytest tests/persistence/test_database.py -v
```

Expected: FAIL because persistence module does not exist.

- [ ] **Step 3: Implement engine/session factory**

Use SQLAlchemy `create_async_engine`, `async_sessionmaker`, and a shared declarative `Base`.

- [ ] **Step 4: Add reusable pytest database fixture**

Fixture should create one isolated temporary SQLite file per test and dispose the engine after yield.

- [ ] **Step 5: Run test and commit**

```bash
pytest tests/persistence/test_database.py -v
git add backend/src/biovolt_backend/persistence backend/tests/conftest.py backend/tests/persistence/test_database.py
git commit -m "feat: add async SQLite database foundation"
```

---

### Task 2: Add telemetry persistence model

**Files:**
- Create: `backend/src/biovolt_backend/persistence/models.py`
- Create: `backend/tests/persistence/test_models.py`

**Interfaces:**
- Produces ORM model `TelemetrySample`.

Required queryable columns:

```text
id
received_at
device_id
cell_id
sequence
uptime_ms
bpv_voltage_mv
current_ua
power_uw
cumulative_energy_mj
od680
temperature_c
lux
grow_led_pwm
mixer_on
control_mode
experiment_id
raw_payload_json
```

Optional raw diagnostic columns may include `adc_raw`, `bpw34_raw`, `bpw34_voltage_mv`.

- [ ] **Step 1: Write failing table-creation test**

Create the database and inspect SQLite table names. Assert `telemetry_samples` exists.

- [ ] **Step 2: Implement ORM model**

Use:
- integer autoincrement primary key
- timezone-aware timestamp represented in Python as `datetime`
- indexed `(device_id, cell_id, received_at)` query path
- nullable derived/sensor columns where the protocol allows null
- `raw_payload_json` as JSON/text audit field

- [ ] **Step 3: Add null-preservation test**

Insert a sample with `temperature_c=None` and assert it reads back as `None`, not `0.0`.

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/persistence/test_models.py -v
git add backend/src/biovolt_backend/persistence/models.py backend/tests/persistence/test_models.py
git commit -m "feat: add telemetry persistence model"
```

---

### Task 3: Implement energy accumulator

**Files:**
- Create: `backend/src/biovolt_backend/domain/energy.py`
- Create: `backend/tests/domain/test_energy.py`

**Interfaces:**
- Produces `EnergyAccumulator.update(device_id: str, cell_id: str, uptime_ms: int, power_uw: float | None) -> float` returning cumulative mJ for current boot session.
- Produces `EnergyAccumulator.reset(device_id: str, cell_id: str) -> None`.

- [ ] **Step 1: Write failing trapezoid test**

```python
import pytest
from biovolt_backend.domain.energy import EnergyAccumulator


def test_energy_uses_trapezoidal_integration():
    acc = EnergyAccumulator()
    assert acc.update("d1", "c1", 0, 10.0) == 0.0
    value = acc.update("d1", "c1", 1000, 20.0)
    assert value == pytest.approx(0.015)
```

Explanation: average power = 15 µW for 1 s = 15 µJ = 0.015 mJ.

- [ ] **Step 2: Add restart test**

```python
def test_uptime_decrease_resets_boot_session_energy():
    acc = EnergyAccumulator()
    acc.update("d1", "c1", 1000, 10.0)
    acc.update("d1", "c1", 2000, 10.0)
    restarted = acc.update("d1", "c1", 100, 10.0)
    assert restarted == 0.0
```

- [ ] **Step 3: Add duplicate-uptime test**

Non-increasing uptime equal to prior uptime must not add energy.

- [ ] **Step 4: Implement accumulator**

Store per-key state:

```python
@dataclass
class _EnergyState:
    uptime_ms: int
    power_uw: float | None
    cumulative_mj: float
```

Update rules:
- first frame initializes state and returns 0
- lower uptime resets
- equal uptime updates latest power but adds no energy
- if either previous/current power is `None`, advance time state without adding energy
- otherwise integrate trapezoid

- [ ] **Step 5: Run tests and commit**

```bash
pytest tests/domain/test_energy.py -v
git add backend/src/biovolt_backend/domain/energy.py backend/tests/domain/test_energy.py
git commit -m "feat: add boot-session energy accumulation"
```

---

### Task 4: Implement persistence throttle

**Files:**
- Create: `backend/src/biovolt_backend/persistence/throttle.py`
- Create: `backend/tests/persistence/test_throttle.py`

**Interfaces:**
- Produces `PersistenceThrottle(interval_seconds: float = 1.0)`.
- Produces `should_persist(device_id: str, cell_id: str, timestamp: datetime) -> bool`.

- [ ] **Step 1: Write failing cadence test**

Use fixed timestamps at `t=0`, `0.5`, `1.0`, `1.5`, `2.0`. Expected decisions: `True, False, True, False, True`.

- [ ] **Step 2: Implement per-device/cell throttle**

Do not use global one-timestamp state, because future Cell A and Cell B telemetry must persist independently.

- [ ] **Step 3: Run test and commit**

```bash
pytest tests/persistence/test_throttle.py -v
git add backend/src/biovolt_backend/persistence/throttle.py backend/tests/persistence/test_throttle.py
git commit -m "feat: throttle telemetry persistence per cell"
```

---

### Task 5: Implement telemetry repository

**Files:**
- Create: `backend/src/biovolt_backend/persistence/telemetry_repository.py`
- Create: `backend/tests/persistence/test_telemetry_repository.py`

**Interfaces:**
- Produces `TelemetryRepository.save(raw, processed, raw_payload) -> TelemetrySample`.
- Produces `latest(device_id: str, cell_id: str) -> TelemetrySample | None`.
- Produces `history(device_id: str, cell_id: str, limit: int) -> list[TelemetrySample]` ordered oldest-to-newest within selected bounded window.

- [ ] **Step 1: Write failing save/latest test**

Insert a processed sample and verify `latest()` returns its sequence and power.

- [ ] **Step 2: Write failing bounded-history test**

Insert 10 rows, request `limit=3`, and assert sequences `[8, 9, 10]` are returned chronologically.

- [ ] **Step 3: Implement repository**

Repository accepts an `async_sessionmaker` in constructor; do not import a global session.

- [ ] **Step 4: Preserve raw payload**

Test `raw_payload_json` can be deserialized and still contains original `sequence`, nested optical fields, and health state.

- [ ] **Step 5: Run persistence suite and commit**

```bash
pytest tests/persistence tests/domain/test_energy.py -v
git add backend/src/biovolt_backend/persistence/telemetry_repository.py backend/tests/persistence/test_telemetry_repository.py
git commit -m "feat: add telemetry repository queries"
```

## Module 1.3 Exit Criteria

- [ ] Async SQLite database can initialize deterministically in tests.
- [ ] `telemetry_samples` preserves raw payload and queryable derived fields.
- [ ] Sensor nulls persist as SQL NULL.
- [ ] Energy accumulation uses every valid incoming frame, not only persisted frames.
- [ ] Uptime reset cannot create negative or inflated energy.
- [ ] Persistence throttle is per device/cell and targets 1 Hz.
- [ ] Latest/history queries are tested and bounded.
- [ ] All persistence/domain tests pass.
