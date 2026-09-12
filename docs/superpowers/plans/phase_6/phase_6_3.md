# Phase 6.3: Backend Adaptive Experiment Orchestration and PWA UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist Adaptive experiment configuration, deliver it through the reliable Phase 4 command path, and provide an operator UX that exposes optimizer ownership/state without presenting unmeasured gain claims.

**Architecture:** Adaptive parameters are part of an experiment arm's immutable start configuration. The experiment orchestrator emits a `set_mode adaptive` command carrying the strict optimizer config. FastAPI stores configuration provenance and exposes current control diagnostics derived from telemetry/device status. The PWA adds Adaptive setup/review and live status but leaves scientific comparison to Phase 7.

**Tech Stack:** FastAPI/Pydantic/SQLAlchemy, existing commands/experiments services, React/TypeScript/Recharts, pytest/Vitest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Adaptive experiment must have a valid Phase 5 calibration revision even though firmware objective does not use calibrated power.
- Adaptive config is immutable after experiment reaches `starting`.
- Backend validates a stricter safe envelope before command creation; ESP32 validates again.
- UI never labels a transient objective change as energy gain.
- UI shows ownership and optimizer state rather than anthropomorphic `AI optimized` claims.
- Manual LED writes remain disabled while arm is Adaptive.

---

### Task 1: Persist Adaptive arm configuration

**Files:**
- Modify: `backend/src/biovolt_backend/experiments/models.py`
- Modify: `backend/src/biovolt_backend/experiments/schemas.py`
- Modify: `backend/src/biovolt_backend/experiments/service.py`
- Test: `backend/tests/experiments/test_adaptive_config.py`

Persist per adaptive arm:

```text
adaptive_initial_pwm
adaptive_pwm_min
adaptive_pwm_max
adaptive_pwm_step
adaptive_settle_ms
adaptive_minimum_valid_samples
adaptive_deadband_fraction
adaptive_mixer_policy
adaptive_mixer_period_ms nullable
adaptive_mixer_on_ms nullable
```

- [ ] **Step 1: Write valid config persistence test**
- [ ] **Step 2: Write invalid bounds/step/settle/deadband tests**
- [ ] **Step 3: Write immutable-after-starting test**
- [ ] **Step 4: Implement validation with shared backend constants mirroring documented firmware limits**
- [ ] **Step 5: Run and commit**

```bash
cd backend
pytest tests/experiments/test_adaptive_config.py -v
git add src/biovolt_backend/experiments tests/experiments/test_adaptive_config.py
git commit -m "feat: persist BioVolt Adaptive experiment configuration"
```

---

### Task 2: Enable Adaptive start orchestration

**Files:**
- Modify: `backend/src/biovolt_backend/experiments/orchestrator.py`
- Modify: `backend/src/biovolt_backend/commands/schemas.py`
- Test: `backend/tests/experiments/test_adaptive_orchestration.py`

Start command payload uses stored immutable arm config. Do not accept optimizer parameters from a separate control POST after start.

- [ ] **Step 1: Write exact command payload test from experiment arm config**
- [ ] **Step 2: Write Adaptive `running` only after applied ack test**
- [ ] **Step 3: Write device rejection -> aborted test**
- [ ] **Step 4: Implement orchestration**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/experiments/test_adaptive_orchestration.py -v
git add src/biovolt_backend/experiments/orchestrator.py src/biovolt_backend/commands/schemas.py tests/experiments/test_adaptive_orchestration.py
git commit -m "feat: orchestrate BioVolt Adaptive experiment start"
```

---

### Task 3: Expose optimizer/control diagnostics without changing scientific ownership

**Files:**
- Create: `backend/src/biovolt_backend/control/status.py`
- Create: `backend/src/biovolt_backend/api/control_status.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Test: `backend/tests/api/test_control_status.py`

Route:

```text
GET /api/control/status?device_id=...&cell_id=...
```

Response may include:

```text
mode
confirmed_grow_led_pwm
confirmed_mixer_on
optimizer_direction
optimizer_state if available from device status extension
optimizer_hold_reason if available
last_telemetry_at
telemetry_age_ms
experiment_id
adaptive_config summary
```

If detailed optimizer state is not in the raw telemetry contract, do not fabricate it. Return only fields actually supported by device/backend state, and keep `optimizer_direction` as the guaranteed minimum.

- [ ] **Step 1: Write Adaptive status test grounded in latest telemetry**
- [ ] **Step 2: Write stale device status test**
- [ ] **Step 3: Implement source-backed status response**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/api/test_control_status.py -v
git add src/biovolt_backend/control/status.py src/biovolt_backend/api/control_status.py src/biovolt_backend/main.py tests/api/test_control_status.py
git commit -m "feat: expose BioVolt adaptive control status"
```

---

### Task 4: Add Adaptive mode to experiment PWA setup

**Files:**
- Modify: `frontend/src/types/experiments.ts`
- Modify: `frontend/src/components/experiments/ExperimentForm.tsx`
- Create: `frontend/src/components/experiments/AdaptiveConfigForm.tsx`
- Create: `frontend/tests/experiments/AdaptiveConfigForm.test.tsx`

Form fields with units/help:
- initial PWM
- min/max PWM
- step
- settling time seconds
- minimum valid samples
- objective deadband percent
- mixer policy off/periodic
- period/on-duration when periodic

- [ ] **Step 1: Write validation boundary tests**
- [ ] **Step 2: Add sensible form defaults while clearly displaying them as configuration, not proven optimum values**
- [ ] **Step 3: Show calibration revision alongside Adaptive config**
- [ ] **Step 4: Disable Manual starting controls for Adaptive arm**
- [ ] **Step 5: Run and commit**

```bash
cd frontend
npm test -- AdaptiveConfigForm
npm run typecheck
git add src/types/experiments.ts src/components/experiments/ExperimentForm.tsx src/components/experiments/AdaptiveConfigForm.tsx tests/experiments/AdaptiveConfigForm.test.tsx
git commit -m "feat: configure BioVolt Adaptive experiments in PWA"
```

---

### Task 5: Add Adaptive start review and live optimizer ownership panel

**Files:**
- Create: `frontend/src/components/experiments/AdaptiveStartReview.tsx`
- Create: `frontend/src/components/control/OptimizerStatusPanel.tsx`
- Modify: `frontend/src/pages/ExperimentDetailPage.tsx`
- Modify: `frontend/src/pages/ControlPage.tsx`
- Test: `frontend/tests/control/OptimizerStatusPanel.test.tsx`

Review copy must explicitly state:

```text
The controller may change grow-light PWM within [min,max].
The controller does not independently change calibration.
The mixer follows the configured off/periodic rule and existing safety cooldowns.
Safe Stop ends Adaptive ownership.
```

Live panel displays:
- Adaptive active/inactive
- confirmed PWM
- optimizer direction: decrease/hold/increase
- telemetry freshness
- current bounds/step/settle
- no gain percentage

- [ ] **Step 1: Write no-gain-metric rendering test**
- [ ] **Step 2: Write direction label tests for -1/0/+1**
- [ ] **Step 3: Write stale telemetry warning test**
- [ ] **Step 4: Disable conflicting manual LED controls while Adaptive active**
- [ ] **Step 5: Run and commit**

```bash
npm test -- OptimizerStatusPanel
npm run typecheck
npm run lint
git add src/components/experiments/AdaptiveStartReview.tsx src/components/control/OptimizerStatusPanel.tsx src/pages/ExperimentDetailPage.tsx src/pages/ControlPage.tsx tests/control/OptimizerStatusPanel.test.tsx
git commit -m "feat: show BioVolt Adaptive ownership and optimizer status"
```

---

### Task 6: Add Adaptive experiment API/PWA integration test

**Files:**
- Create: `backend/tests/integration/test_adaptive_experiment.py`
- Create: `frontend/tests/integration/adaptiveExperimentFlow.test.tsx`

Backend sequence:

```text
create calibrated Adaptive experiment
ready
start
verify adaptive config command
ack applied
running
telemetry optimizer_direction changes are accepted
safe stop
completed
```

Frontend sequence verifies `starting -> running`, optimizer panel, conflicting controls disabled, and no gain claim.

- [ ] **Step 1: Implement backend integration test**
- [ ] **Step 2: Implement frontend integration test**
- [ ] **Step 3: Run suites and commit**

```bash
cd backend && pytest tests/integration/test_adaptive_experiment.py -v
cd ../frontend && npm test -- adaptiveExperimentFlow && npm run typecheck
git add backend/tests/integration/test_adaptive_experiment.py frontend/tests/integration/adaptiveExperimentFlow.test.tsx
git commit -m "test: verify BioVolt Adaptive experiment orchestration"
```

## Module 6.3 Exit Criteria

- [ ] Adaptive config is persisted and immutable after start begins.
- [ ] Backend command payload comes from persisted experiment config.
- [ ] Adaptive running state still requires device applied ack.
- [ ] UI shows constraints/ownership/status without a fabricated improvement number.
- [ ] Conflicting Manual LED controls are unavailable while Adaptive owns the actuator.
- [ ] Control status is source-backed and visibly stale when telemetry is stale.
