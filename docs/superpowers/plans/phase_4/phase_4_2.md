# Phase 4.2: Experiment Persistence and Lifecycle API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist experiment definitions and enforce an explicit lifecycle so a BioVolt run cannot enter `running` or `completed` through ad-hoc API writes.

**Architecture:** Experiment state is modeled in SQLite with a small domain state machine. REST handlers call an `ExperimentService`; handlers never update state columns directly. An experiment contains one or more arms so the same model later supports passive/adaptive comparisons without requiring two specific physical device IDs.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x async ORM, SQLite, pytest, pytest-asyncio.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Phase 4 modes allowed for execution are `monitor`, `passive`, and `manual`.
- `adaptive` may be stored only as a future enum value but start must reject it until Phase 6.
- Completed/aborted experiments are measurement records and may not have device/mode/setpoint fields rewritten.
- Notes may be edited after completion only through a dedicated notes field.
- Experiment timestamps are backend UTC timestamps.
- Phase 5 later adds immutable calibration binding; Phase 4 schema leaves the extension point nullable but does not fake calibration.

---

### Task 1: Add experiment ORM models

**Files:**
- Create: `backend/src/biovolt_backend/experiments/models.py`
- Create: `backend/src/biovolt_backend/experiments/__init__.py`
- Modify: `backend/src/biovolt_backend/persistence/database.py`
- Test: `backend/tests/experiments/test_models.py`

**Interfaces:**

`Experiment` columns:

```text
id UUID text primary key
name text
state text
description nullable text
created_at datetime
updated_at datetime
started_at nullable datetime
ended_at nullable datetime
notes nullable text
calibration_profile_id nullable text
```

`ExperimentArm` columns:

```text
id UUID text primary key
experiment_id FK
device_id text
cell_id text
mode text
initial_led_pwm integer
initial_mixer_on boolean
label nullable text
```

- [ ] **Step 1: Write failing table-creation test**
- [ ] **Step 2: Implement ORM models and uniqueness on `(experiment_id, device_id, cell_id)`**
- [ ] **Step 3: Add relationship loading test**
- [ ] **Step 4: Run tests**

```bash
cd backend
pytest tests/experiments/test_models.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/biovolt_backend/experiments src/biovolt_backend/persistence/database.py tests/experiments/test_models.py
git commit -m "feat: persist BioVolt experiments and arms"
```

---

### Task 2: Implement experiment domain state machine

**Files:**
- Create: `backend/src/biovolt_backend/experiments/state.py`
- Test: `backend/tests/experiments/test_state.py`

**Interfaces:**

```python
class ExperimentState(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ABORTED = "aborted"


def can_transition(current: ExperimentState, target: ExperimentState) -> bool: ...
```

Allowed transitions:

```text
draft -> ready
ready -> draft
ready -> starting
starting -> running
starting -> aborted
running -> stopping
running -> aborted
stopping -> completed
stopping -> aborted
```

- [ ] **Step 1: Write parameterized allowed-transition tests**
- [ ] **Step 2: Write terminal-state rejection tests**
- [ ] **Step 3: Implement pure transition table**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/experiments/test_state.py -v
git add src/biovolt_backend/experiments/state.py tests/experiments/test_state.py
git commit -m "feat: enforce BioVolt experiment state transitions"
```

---

### Task 3: Add repository and service validation

**Files:**
- Create: `backend/src/biovolt_backend/experiments/repository.py`
- Create: `backend/src/biovolt_backend/experiments/schemas.py`
- Create: `backend/src/biovolt_backend/experiments/service.py`
- Test: `backend/tests/experiments/test_service.py`

**Interfaces:**

```python
class ExperimentService:
    async def create(self, request: ExperimentCreate) -> ExperimentView: ...
    async def update_draft(self, experiment_id: str, request: ExperimentDraftUpdate) -> ExperimentView: ...
    async def mark_ready(self, experiment_id: str) -> ExperimentView: ...
    async def begin_start(self, experiment_id: str) -> ExperimentView: ...
    async def mark_running(self, experiment_id: str) -> ExperimentView: ...
    async def begin_stop(self, experiment_id: str) -> ExperimentView: ...
    async def mark_completed(self, experiment_id: str) -> ExperimentView: ...
    async def abort(self, experiment_id: str, reason: str | None) -> ExperimentView: ...
```

Ready validation:
- at least one arm
- non-empty device/cell
- mode is `passive` or `manual` for Phase 4 executable experiments
- initial PWM in `0..255`
- no duplicate device/cell arm

- [ ] **Step 1: Write failing create/read test**
- [ ] **Step 2: Write failing ready-validation tests**
- [ ] **Step 3: Implement repository and service**
- [ ] **Step 4: Add immutable-terminal-field test**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/experiments -v
git add src/biovolt_backend/experiments tests/experiments
git commit -m "feat: add BioVolt experiment lifecycle service"
```

---

### Task 4: Add experiment REST API

**Files:**
- Create: `backend/src/biovolt_backend/api/experiments.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Test: `backend/tests/api/test_experiments.py`

**Routes:**

```text
POST  /api/experiments
GET   /api/experiments
GET   /api/experiments/{id}
PATCH /api/experiments/{id}
POST  /api/experiments/{id}/ready
POST  /api/experiments/{id}/start
POST  /api/experiments/{id}/stop
POST  /api/experiments/{id}/abort
```

At this module, `start` moves `ready -> starting` and delegates actual command dispatch to Module 4.3. Do not mark running in the route.

- [ ] **Step 1: Write API tests for create/list/get/update/ready**
- [ ] **Step 2: Write test that start returns `starting`, never `running` before ack**
- [ ] **Step 3: Implement router using service only**
- [ ] **Step 4: Run API suite**

```bash
pytest tests/api/test_experiments.py -v
```

- [ ] **Step 5: Commit**

```bash
git add src/biovolt_backend/api/experiments.py src/biovolt_backend/main.py tests/api/test_experiments.py
git commit -m "feat: expose BioVolt experiment lifecycle API"
```

## Module 4.2 Exit Criteria

- [ ] Experiment/arm records persist across backend restart.
- [ ] State machine rejects illegal transitions.
- [ ] Ready validation rejects incomplete arms.
- [ ] Adaptive start is unavailable in Phase 4.
- [ ] `POST /start` cannot directly create a running experiment.
- [ ] Completed/aborted measurement-defining fields are immutable.
