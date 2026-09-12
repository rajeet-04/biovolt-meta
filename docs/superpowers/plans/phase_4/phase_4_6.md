# Phase 4.6: End-to-End Command and Experiment Reliability Acceptance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that operator intent travels through the complete PWA -> FastAPI -> `/ws/device` -> ESP32 -> acknowledgement path without stale replay, duplicate side effects, false experiment state, or safety bypass.

**Architecture:** Acceptance uses two device implementations against the same backend contract: the deterministic Python simulator for reproducible CI and the real ESP32 for HIL. The simulator gains command/ack behavior only as test infrastructure and must not create simulator-specific backend branches.

**Tech Stack:** Existing simulator, FastAPI integration tests, React/Vitest, PlatformIO hardware smoke, Docker Compose.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Simulator and ESP32 use identical command/ack schemas.
- Backend remains unaware of source type.
- Real-hardware acceptance cannot be replaced by simulator CI.
- No test may mark an experiment running by directly editing the database.
- All write-path acceptance begins through the same protected REST endpoints used by the PWA.
- Every negative-path test verifies final hardware/telemetry state, not only HTTP status.

---

### Task 1: Add simulator command/ack parity

**Files:**
- Modify: `simulator/src/biovolt_simulator/client.py`
- Create: `simulator/src/biovolt_simulator/commands.py`
- Create: `simulator/tests/test_commands.py`

Simulator state:

```text
mode
led_pwm
mixer_on
seen_command_ids bounded cache
```

Rules match Phase 4 ESP32 policy:
- monitor/passive/manual allowed
- adaptive rejected
- mixer command allowed only manual
- duplicate command returns same terminal ack
- safe stop -> monitor, LED 0, mixer false

- [ ] **Step 1: Write set-mode/set-PWM/safe-stop tests**
- [ ] **Step 2: Write duplicate command ID side-effect test**
- [ ] **Step 3: Write adaptive rejection test**
- [ ] **Step 4: Implement simulator parity using shared examples/schema validation**
- [ ] **Step 5: Run and commit**

```bash
pytest simulator/tests/test_commands.py -v
git add simulator/src/biovolt_simulator simulator/tests/test_commands.py
git commit -m "test: add BioVolt simulator command acknowledgement parity"
```

---

### Task 2: Add backend command lifecycle integration tests

**Files:**
- Create: `backend/tests/integration/test_command_lifecycle.py`

Scenarios:

```text
1. authenticated device connected
2. operator session created
3. POST control command
4. command delivered
5. device sends applied ack
6. GET command shows applied
7. processed telemetry confirms resulting device state
```

Negative scenarios:
- wrong operator session
- disconnected device until command expiry
- device rejection
- duplicate ack
- duplicate command delivery

- [ ] **Step 1: Implement applied lifecycle test**
- [ ] **Step 2: Implement expiry/no-late-send test**
- [ ] **Step 3: Implement duplicate-delivery idempotency test**
- [ ] **Step 4: Run integration suite and commit**

```bash
cd backend
pytest tests/integration/test_command_lifecycle.py -v
git add tests/integration/test_command_lifecycle.py
git commit -m "test: verify BioVolt command lifecycle end to end"
```

---

### Task 3: Add experiment start/stop integration test

**Files:**
- Create: `backend/tests/integration/test_experiment_control.py`

Test exact state sequence:

```text
draft -> ready -> starting -> running -> stopping -> completed
```

Assertions:
- `starting` remains until all required command acks are applied
- telemetry after running reflects requested passive/manual state
- stop creates safe-stop command
- completed only after safe-stop applied

- [ ] **Step 1: Implement single-arm passive experiment test**
- [ ] **Step 2: Implement two-arm all-acks-required test**
- [ ] **Step 3: Implement rejection during start -> aborted test**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/integration/test_experiment_control.py -v
git add tests/integration/test_experiment_control.py
git commit -m "test: verify BioVolt experiment command orchestration"
```

---

### Task 4: Add PWA control integration tests

**Files:**
- Create: `frontend/tests/integration/operatorControlFlow.test.tsx`

Mock API/WebSocket sequence:

```text
login success
create experiment
mark ready
start -> starting
command pending
backend later returns running
stop -> stopping
backend later returns completed
```

Also test command rejection and stale device.

- [ ] **Step 1: Write no-optimistic-running test**
- [ ] **Step 2: Write rejected command visible to operator test**
- [ ] **Step 3: Write offline control disabled test**
- [ ] **Step 4: Run frontend suite and commit**

```bash
cd frontend
npm test -- operatorControlFlow
npm run typecheck
npm run lint
git add tests/integration/operatorControlFlow.test.tsx
git commit -m "test: verify BioVolt operator control states"
```

---

### Task 5: Add real ESP32 command HIL checklist

**Files:**
- Create: `scripts/phase4_control_hil.md`

Required manual sequence:

```text
1. simulator stopped
2. real ESP32 connected
3. verify monitor / PWM 0 / mixer OFF
4. operator login
5. set manual mode
6. set LED PWM to a safe low test value
7. confirm command applied and telemetry matches
8. request mixer ON only if physical driver/load is safe to test
9. verify cooldown rejection by attempting early restart
10. Safe Stop
11. verify mode monitor / PWM 0 / mixer OFF
```

Record:

```text
command_id
requested state
ack status
ack uptime_ms
telemetry sequence after ack
observed applied state
```

- [ ] **Step 1: Write pre-power/load safety warning**
- [ ] **Step 2: Add exact expected acknowledgements**
- [ ] **Step 3: Execute on real hardware and attach results to PR notes**
- [ ] **Step 4: Commit checklist**

```bash
git add scripts/phase4_control_hil.md
git commit -m "docs: add Phase 4 real hardware control acceptance"
```

---

### Task 6: Add reconnect and expiry acceptance

**Files:**
- Modify: `scripts/phase4_control_hil.md`

Procedure:

```text
A. create short-TTL command while device disconnected
B. wait beyond expiry
C. reconnect device
D. verify command never applies

E. create valid command
F. force socket drop after possible send but before backend sees ack
G. reconnect while command still unexpired
H. allow duplicate delivery if backend retries
I. verify physical effect happened at most once and terminal ack correlates to same command_id
```

- [ ] **Step 1: Add procedure and record template**
- [ ] **Step 2: Execute with real ESP32**
- [ ] **Step 3: Verify final telemetry state and command audit table**
- [ ] **Step 4: Commit observed acceptance notes in PR, not hard-coded result claims in repository**

---

### Task 7: Phase 4 regression gate

Run:

```bash
pytest shared/tests -v
cd backend && pytest -v
cd ../simulator && pytest -v
cd ../frontend && npm test && npm run typecheck && npm run lint && npm run build
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
```

- [ ] **Step 1: Run complete software regression**
- [ ] **Step 2: Run real ESP32 HIL checklist**
- [ ] **Step 3: Confirm no `adaptive` command is accepted**
- [ ] **Step 4: Confirm no command secret/session token appears in logs**

## Module 4.6 Exit Criteria

- [ ] Simulator command parity supports deterministic CI without backend branching.
- [ ] Real ESP32 receives and acknowledges commands on unchanged `/ws/device`.
- [ ] Experiment start/stop state follows actual device outcomes.
- [ ] Duplicate delivery causes at most one physical side effect.
- [ ] Expired disconnected command never applies after reconnect.
- [ ] PWA displays command failures and does not queue offline writes.
- [ ] Safe Stop results in monitor mode, PWM 0, mixer OFF.
- [ ] Full Phase 0 to 4 regression passes.
