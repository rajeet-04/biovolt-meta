# Phase 4.3: Backend Command Dispatcher and Acknowledgement Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist outbound device commands, deliver them over the existing `/ws/device` connection, correlate acknowledgements, enforce command expiry, and drive experiment lifecycle transitions only from confirmed device outcomes.

**Architecture:** A `CommandService` owns command creation/state transitions and persists every command. `DeviceConnectionRegistry` gains an outbound send primitive but does not own business logic. Incoming `/ws/device` messages are classified by `schema_version` as telemetry or acknowledgement and routed to the corresponding service. Expired commands are never sent or retried.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x async ORM, SQLite, asyncio, jsonschema, pytest-asyncio.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Commands are persisted before network send.
- `applied` is set only from a valid device acknowledgement.
- Backend UTC controls `expires_at` send eligibility.
- Commands are not retried after terminal state or expiry.
- One command may be delivered more than once only when the previous send outcome is unknown and the command is still valid; device idempotency makes duplicate delivery safe.
- Command state transitions are monotonic.
- Unknown or mismatched `command_id` acknowledgements are recorded as protocol errors and do not mutate another command.
- Acknowledgement `device_id` must match the command device.
- Experiment transitions are performed in one service layer, not inside WebSocket handler code.

---

### Task 1: Add command persistence model and repository

**Files:**
- Create: `backend/src/biovolt_backend/commands/models.py`
- Create: `backend/src/biovolt_backend/commands/repository.py`
- Create: `backend/src/biovolt_backend/commands/__init__.py`
- Test: `backend/tests/commands/test_repository.py`

**Command columns:**

```text
id command_id UUID text primary key
device_id text
experiment_id nullable text
kind text
payload_json text
status text
issued_at datetime
expires_at datetime
sent_at nullable datetime
accepted_at nullable datetime
terminal_at nullable datetime
reason_code nullable text
message nullable text
applied_state_json nullable text
send_attempts integer default 0
```

Allowed statuses:

```text
queued
sent
accepted
applied
rejected
failed
expired
```

- [ ] **Step 1: Write failing save/latest-status tests**
- [ ] **Step 2: Implement ORM model and repository**
- [ ] **Step 3: Add query for non-terminal unexpired commands by device ordered by issued time**
- [ ] **Step 4: Run tests and commit**

```bash
cd backend
pytest tests/commands/test_repository.py -v
git add src/biovolt_backend/commands tests/commands/test_repository.py
git commit -m "feat: persist BioVolt device commands"
```

---

### Task 2: Implement command state machine and service

**Files:**
- Create: `backend/src/biovolt_backend/commands/state.py`
- Create: `backend/src/biovolt_backend/commands/service.py`
- Create: `backend/src/biovolt_backend/commands/schemas.py`
- Test: `backend/tests/commands/test_service.py`

**Interfaces:**

```python
class CommandService:
    async def create(self, request: CommandCreate) -> CommandView: ...
    async def mark_sent(self, command_id: str) -> CommandView: ...
    async def apply_ack(self, ack: DeviceAck) -> CommandView: ...
    async def expire_due(self, now: datetime) -> int: ...
    async def get(self, command_id: str) -> CommandView: ...
```

State rules:

```text
queued -> sent
sent -> accepted
sent -> applied/rejected/failed
accepted -> applied/rejected/failed
queued/sent/accepted -> expired
```

- [ ] **Step 1: Write failing state-transition tests**
- [ ] **Step 2: Write mismatched-device acknowledgement test**
- [ ] **Step 3: Write duplicate terminal acknowledgement idempotency test**
- [ ] **Step 4: Implement service and monotonic transition validation**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/commands/test_service.py -v
git add src/biovolt_backend/commands tests/commands/test_service.py
git commit -m "feat: track BioVolt command acknowledgement state"
```

---

### Task 3: Extend device connection registry with outbound delivery

**Files:**
- Modify: `backend/src/biovolt_backend/websockets/device_registry.py`
- Test: `backend/tests/websockets/test_device_registry.py`

**Interfaces:**

```python
async def send_json(self, device_id: str, payload: dict) -> bool: ...
```

Return `False` when device is not currently connected; do not block waiting for reconnect.

- [ ] **Step 1: Write failing connected-send test**
- [ ] **Step 2: Write disconnected returns-false test**
- [ ] **Step 3: Serialize once and send under per-connection lock**
- [ ] **Step 4: Do not hold global registry lock during network write**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/websockets/test_device_registry.py -v
git add src/biovolt_backend/websockets/device_registry.py tests/websockets/test_device_registry.py
git commit -m "feat: add outbound device websocket delivery"
```

---

### Task 4: Implement command dispatcher

**Files:**
- Create: `backend/src/biovolt_backend/commands/dispatcher.py`
- Test: `backend/tests/commands/test_dispatcher.py`

**Interfaces:**

```python
class CommandDispatcher:
    async def dispatch(self, command_id: str) -> CommandView: ...
    async def dispatch_pending_for_device(self, device_id: str) -> int: ...
```

Dispatch algorithm:

```text
load command
if terminal -> return unchanged
if now >= expires_at -> mark expired
if device disconnected -> leave queued/sent as-is, no busy loop
if connected -> send schema payload -> mark sent + increment attempt
```

Reconnect rule:
- when a device reconnects, call `dispatch_pending_for_device`
- only unexpired commands are considered
- terminal commands are ignored

- [ ] **Step 1: Write connected dispatch test**
- [ ] **Step 2: Write disconnected command remains non-terminal test**
- [ ] **Step 3: Write expiry-before-send test**
- [ ] **Step 4: Write reconnect does not resend expired command test**
- [ ] **Step 5: Implement and commit**

```bash
pytest tests/commands/test_dispatcher.py -v
git add src/biovolt_backend/commands/dispatcher.py tests/commands/test_dispatcher.py
git commit -m "feat: dispatch BioVolt device commands with expiry"
```

---

### Task 5: Route acknowledgement messages on `/ws/device`

**Files:**
- Modify: `backend/src/biovolt_backend/api/ws_device.py`
- Modify: `backend/src/biovolt_backend/contracts/loader.py`
- Test: `backend/tests/integration/test_device_ack_websocket.py`

Message classification:

```python
schema_version = payload.get("schema_version")
if schema_version == "device-telemetry.v1": ...
elif schema_version == "device-ack.v1": ...
else: reject protocol message
```

- [ ] **Step 1: Write failing authenticated ack integration test**
- [ ] **Step 2: Validate acknowledgement against shared schema before Pydantic parsing**
- [ ] **Step 3: Apply ack through `CommandService` only**
- [ ] **Step 4: Reject device ID mismatch between auth header and ack body**
- [ ] **Step 5: Run integration test and commit**

```bash
pytest tests/integration/test_device_ack_websocket.py -v
git add src/biovolt_backend/api/ws_device.py src/biovolt_backend/contracts/loader.py tests/integration/test_device_ack_websocket.py
git commit -m "feat: receive BioVolt command acknowledgements"
```

---

### Task 6: Bind command outcomes to experiment transitions

**Files:**
- Create: `backend/src/biovolt_backend/experiments/orchestrator.py`
- Modify: `backend/src/biovolt_backend/experiments/service.py`
- Modify: `backend/src/biovolt_backend/api/experiments.py`
- Test: `backend/tests/experiments/test_orchestrator.py`

Start orchestration for one arm:

```text
ready -> starting
create set_mode command
create initial set_led_pwm command
create initial set_mixer command only when needed
wait asynchronously via later ack events, not HTTP request blocking
all required commands applied -> running
any required command rejected/failed/expired -> aborted
```

Stop orchestration:

```text
running -> stopping
safe_stop command
applied -> completed
rejected/failed/expired -> aborted
```

For multiple arms, all required arm commands must apply before `running`.

- [ ] **Step 1: Write start stays `starting` until all required acks test**
- [ ] **Step 2: Write one-arm rejection causes experiment abort test**
- [ ] **Step 3: Write safe-stop applied causes completed test**
- [ ] **Step 4: Implement orchestrator event hook from `CommandService.apply_ack`**
- [ ] **Step 5: Run experiment/command suites and commit**

```bash
pytest tests/experiments tests/commands tests/integration/test_device_ack_websocket.py -v
git add src/biovolt_backend/experiments src/biovolt_backend/commands src/biovolt_backend/api/experiments.py tests/experiments/test_orchestrator.py
git commit -m "feat: drive experiment state from device command outcomes"
```

---

### Task 7: Expose command status API

**Files:**
- Create: `backend/src/biovolt_backend/api/commands.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Test: `backend/tests/api/test_commands.py`

Route:

```text
GET /api/commands/{command_id}
```

Response contains persisted status and safe applied-state fields only; do not expose device token or operator secrets.

- [ ] **Step 1: Write queued/applied response tests**
- [ ] **Step 2: Implement router**
- [ ] **Step 3: Run API tests**
- [ ] **Step 4: Commit**

```bash
pytest tests/api/test_commands.py -v
git add src/biovolt_backend/api/commands.py src/biovolt_backend/main.py tests/api/test_commands.py
git commit -m "feat: expose BioVolt command status API"
```

## Module 4.3 Exit Criteria

- [ ] Commands are durable before send.
- [ ] Ack device identity is verified.
- [ ] Duplicate terminal ack is idempotent.
- [ ] Expired command cannot be resent on reconnect.
- [ ] Experiment start waits for all required applied acknowledgements.
- [ ] Experiment aborts on required command rejection/failure/expiry.
- [ ] HTTP start/stop calls never wait synchronously for device response.
