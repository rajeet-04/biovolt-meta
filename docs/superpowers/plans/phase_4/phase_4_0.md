# Phase 4 Overview: Experiment Lifecycle, Reliable Commands, and Operator Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe bidirectional control substrate that lets FastAPI orchestrate experiments and lets an authenticated operator use Passive and Manual modes while every hardware-changing command is explicitly acknowledged by the ESP32.

**Architecture:** Phase 4 expands the stable Phase 0 to 3 device boundary with versioned server-to-device command and device-to-server acknowledgement envelopes on the existing `/ws/device` socket. FastAPI persists experiments and command state, the ESP32 validates and safety-gates every command before application, and the PWA exposes experiment/control workflows only after a lightweight operator session is established. Adaptive P&O remains disabled until Phase 6.

**Tech Stack:** Existing FastAPI/Pydantic/SQLAlchemy/SQLite backend, existing ESP32 PlatformIO/Arduino/FreeRTOS firmware, React/TypeScript PWA, JSON Schema contracts, pytest/Vitest/PlatformIO Unity.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 3 real-device parity and telemetry-gap safety.

## Global Constraints

- Continue using the single authenticated `WS /ws/device` connection for both telemetry and command traffic.
- Do not add a second hardware-only control WebSocket.
- Commands are server-to-device messages; acknowledgements are device-to-server messages.
- Every command has a globally unique `command_id` and a finite expiry.
- A command that is expired, malformed, unsupported, or unsafe must be rejected without changing hardware.
- Repeated delivery of the same `command_id` must be idempotent.
- FastAPI must not mark a command `applied` merely because it was sent. Only an ESP32 `applied` acknowledgement may do that.
- Operator-facing controls must show `pending`, `applied`, `rejected`, `failed`, or `expired` states.
- Remote actuator writes require an authenticated operator session.
- Read-only monitoring remains available without operator login on the local dashboard.
- Phase 4 enables only `monitor`, `passive`, and `manual` control semantics. `adaptive` remains unavailable.
- Manual commands still pass through the ESP32 safety layer and cannot bypass PWM bounds, mixer runtime, or cooldown.
- Experiment state is persisted in SQLite and survives backend restart.
- Commands have bounded retry/expiry semantics. Do not replay stale commands indefinitely after a reconnect.
- Device secrets remain header-based and operator credentials remain server-side. No PIN or operator session secret is placed in frontend source code.
- Public Cloudflared exposure is still out of scope until Phase 8.

---

## Phase 4 Experiment State Machine

```text
draft
  |
  v
ready
  |
  v
starting
  |  device command applied
  v
running
  |
  v
stopping
  |  safe monitor/off command applied
  v
completed
```

Failure branches:

```text
starting -> aborted
running  -> aborted
stopping -> aborted
```

Rules:
- `draft` may be edited.
- `ready` has complete device/cell/mode/setpoint selection.
- `starting` is waiting for required command acknowledgement.
- `running` begins only after the device has acknowledged the required mode/setpoint command as applied.
- `completed` is immutable except for notes/labels that do not alter measurements.
- An experiment cannot be silently re-used after completion; create a new experiment/run.

Phase 5 later binds an immutable calibration profile snapshot at experiment start.

---

## Phase 4 Command Model

Initial command kinds:

```text
set_mode
set_led_pwm
set_mixer
request_status
safe_stop
```

Allowed Phase 4 modes:

```text
monitor
passive
manual
```

`adaptive` is represented in the shared enum for forward compatibility but the Phase 4 backend and firmware reject attempts to activate it with `phase_not_available`.

Command terminal states:

```text
applied
rejected
failed
expired
```

Non-terminal states:

```text
queued
sent
accepted
```

The device may emit `accepted` when parsing succeeds and `applied` only after the requested state has actually passed safety validation and been written to the actuator controller.

---

## Module Map

### Module 4.1: Shared Command and Acknowledgement Contracts
Plan: `docs/superpowers/plans/phase_4/phase_4_1.md`

Produces:
- `device-command.v1` JSON Schema
- `device-ack.v1` JSON Schema
- canonical examples
- protocol documentation
- contract tests

### Module 4.2: Experiment Persistence and Lifecycle API
Plan: `docs/superpowers/plans/phase_4/phase_4_2.md`

Produces:
- `experiments` and `experiment_arms` persistence
- explicit experiment state machine
- create/read/start/stop/abort APIs
- validation for Passive/Manual modes
- experiment lifecycle tests

### Module 4.3: Backend Command Dispatcher and Ack Tracking
Plan: `docs/superpowers/plans/phase_4/phase_4_3.md`

Produces:
- command persistence
- connected-device outbound queue
- TTL/expiry handling
- ack correlation and idempotency
- experiment transition orchestration
- command status REST API

### Module 4.4: ESP32 Command Parsing, Safety Application, and Acknowledgement
Plan: `docs/superpowers/plans/phase_4/phase_4_4.md`

Produces:
- versioned command parser
- bounded command queue
- command-ID dedupe cache
- Passive and Manual local semantics
- actual applied-state acknowledgements
- explicit rejection of Adaptive mode

### Module 4.5: Operator PIN Session and PWA Experiment/Control UX
Plan: `docs/superpowers/plans/phase_4/phase_4_5.md`

Produces:
- operator login/logout/status endpoints
- server-side expiring sessions
- protected write APIs
- `/experiments` and `/control` PWA routes
- command pending/applied/rejected UX
- confirmation and accessibility tests

### Module 4.6: End-to-End Control Reliability Acceptance
Plan: `docs/superpowers/plans/phase_4/phase_4_6.md`

Produces:
- simulator command/ack support for test parity
- real ESP32 command smoke
- duplicate-command test
- timeout/reconnect test
- experiment start/stop acceptance
- Phase 4 CI and acceptance checklist

---

## Planned REST Surface

Read operations:

```text
GET  /api/experiments
GET  /api/experiments/{experiment_id}
GET  /api/commands/{command_id}
GET  /api/operator/session
```

Protected writes:

```text
POST /api/operator/login
POST /api/operator/logout
POST /api/experiments
PATCH /api/experiments/{experiment_id}
POST /api/experiments/{experiment_id}/ready
POST /api/experiments/{experiment_id}/start
POST /api/experiments/{experiment_id}/stop
POST /api/experiments/{experiment_id}/abort
POST /api/control/led
POST /api/control/mixer
POST /api/control/mode
```

All control endpoints return a command resource rather than optimistic actuator success.

Example response:

```json
{
  "command_id": "7b0a82c6-55c6-4af2-8aac-8dbf93ee3a17",
  "status": "queued",
  "expires_at": "2026-08-23T13:10:30Z"
}
```

The UI follows the command until a terminal status arrives.

---

## Operator Security Model

Use a deliberately small local security model:

```text
BIOVOLT_OPERATOR_PIN_HASH in backend environment
        |
        v
POST /api/operator/login
        |
        v
random opaque session token
        |
        v
HttpOnly + SameSite=Strict cookie
        |
        v
server-side expiring session store
```

Requirements:
- compare PIN using a slow password hash, preferably Argon2 via `argon2-cffi`
- session lifetime: 30 minutes absolute maximum for Phase 4
- logout invalidates server-side token
- backend restart may invalidate sessions; this is acceptable for the hackathon
- failed login returns a generic error and never reveals PIN hash configuration
- state-changing routes require a valid operator session

Do not build account registration, roles, password reset, OAuth, or JWT infrastructure.

---

## Product Design Rules

The Phase 4 UI must make control state explicit:

```text
operator intent -> command pending -> device applied/rejected
```

Never skip directly from a button click to a green success state.

Minimum routes:

```text
/experiments
/experiments/:experimentId
/control
```

Experiment-start confirmation shows:
- experiment name
- device/cell
- mode
- fixed PWM/setpoint values when Passive
- selected Manual starting state when applicable
- current device connection/freshness

Manual control page separates monitoring from actuation and labels the last confirmed device state.

---

## Planned Commit Sequence

1. `feat: define BioVolt device command and acknowledgement contracts`
2. `feat: persist BioVolt experiment lifecycle`
3. `feat: dispatch commands and track device acknowledgements`
4. `feat: execute safe remote commands on ESP32`
5. `feat: add protected experiment and manual-control workflows`
6. `test: verify BioVolt command and experiment reliability`

## Phase 4 Exit Criteria

- [ ] Shared command and ack schemas validate canonical examples.
- [ ] Existing telemetry contract remains unchanged.
- [ ] Experiment state transitions are explicitly tested.
- [ ] `running` is entered only after required command acknowledgement is `applied`.
- [ ] Device disconnect while starting cannot falsely mark an experiment running.
- [ ] Duplicate `command_id` does not repeat actuator side effects.
- [ ] Expired command is never applied.
- [ ] Unsupported/unsafe command returns a rejection acknowledgement.
- [ ] Manual PWM remains bounded by firmware safety policy.
- [ ] Mixer runtime/cooldown cannot be bypassed remotely.
- [ ] Adaptive mode activation is rejected in Phase 4.
- [ ] Operator write APIs reject unauthenticated requests.
- [ ] PWA displays command pending/applied/rejected/expired states.
- [ ] Backend restart preserves experiment records and command audit history.
- [ ] ESP32 reconnect does not cause stale expired commands to execute.
- [ ] Real-device start/stop experiment smoke passes.
- [ ] Phase 0 to 3 regression suites remain green.

## Handoff to Phase 5

Phase 5 adds versioned calibration profiles and binds one immutable calibration snapshot to each experiment before scientific biomass/carbon values become eligible for display.
