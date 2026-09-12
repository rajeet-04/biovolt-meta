# Phase 6 Overview: Adaptive Perturb & Observe Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable BioVolt Adaptive mode by adding a local ESP32 Perturb & Observe controller that adjusts grow-light PWM to seek higher BPV electrical output while preserving all Phase 3/4 safety, command, telemetry, and offline guarantees.

**Architecture:** The optimizer is a pure host-testable state machine embedded in the ESP32 ControlTask. It receives fresh BPV voltage observations, optimizes a local voltage-squared objective, and requests bounded grow-light PWM changes through the existing actuator-safety path. FastAPI starts/stops Adaptive experiments and sends high-level optimizer configuration; it does not run the 500 ms optimization loop. Mixer control remains an independent threshold/cooldown rule and is not an optimization variable in the MVP.

**Tech Stack:** PlatformIO/C++17, FreeRTOS, existing BioVoltCore host tests, FastAPI experiment/command services, React/TypeScript PWA.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 5 calibrated experiment substrate and Phase 4 reliable command/ack path.

## Global Constraints

- Adaptive activation is allowed only after Phase 6 is implemented and tested.
- Optimizer may change grow-light PWM only.
- Mixer remains outside the P&O search space.
- The local objective is `bpv_voltage_mv^2`, not a firmware-computed `power_uw` field.
- For one fixed positive load resistance, maximizing `V^2` is mathematically equivalent to maximizing `V^2/R`, so the optimizer need not know the calibration resistance.
- Raw telemetry remains `device-telemetry.v1` and still carries no `power_uw`.
- `optimizer_direction` becomes meaningful as `-1`, `0`, or `+1`.
- Invalid/stale BPV measurements suspend perturbation.
- PWM always remains inside configured safety bounds.
- Every perturbation waits for a settling window before comparing the objective.
- Manual or Safe Stop command immediately suspends/resets Adaptive control.
- Device network loss does not stop the local optimizer during an already-running Adaptive experiment unless the configured offline policy says to fail safe. MVP policy: continue the last valid Adaptive configuration locally while safety remains active.
- Device reboot does not silently resume Adaptive from NVS. It boots Monitor-safe and requires new experiment orchestration.
- The optimizer does not calculate or publish percent improvement. Phase 7 computes measured experiment comparisons from persisted data.

---

## MVP P&O State Model

```text
Inactive
   |
   | Adaptive enabled with valid config
   v
Initialize
   |
   | valid observation
   v
Perturb
   |
   | apply PWM +/- step
   v
Settle
   |
   | wait configured settling interval
   v
Observe
   |
   +-- objective improved -> keep direction -> Perturb
   |
   +-- objective worsened -> reverse direction -> Perturb
   |
   +-- objective unavailable -> Hold
   v
Hold
   |
   +-- valid data returns -> Observe/Initialize
   +-- mode leaves adaptive -> Inactive
```

Bounds:

```text
pwm_min <= grow_led_pwm <= pwm_max
```

At a bound, the controller reverses or holds rather than repeatedly requesting impossible PWM values.

---

## Adaptive Configuration

High-level configuration stored with the experiment arm and sent at Adaptive start:

```text
initial_pwm
pwm_min
pwm_max
pwm_step
settle_ms
minimum_valid_samples
objective_deadband_fraction
```

Recommended MVP defaults are configuration values, not hard scientific truths. They must be visible in the experiment record and adjustable only within safe server/device limits.

Validation:
- `pwm_min < pwm_max`
- `initial_pwm` within bounds
- `pwm_step > 0` and <= configured maximum safe step
- `settle_ms >= 500`
- `minimum_valid_samples >= 1`
- deadband finite and >= 0

No auto-tuning of these parameters in Phase 6.

---

## Objective and Comparison

For each evaluation window, the optimizer uses robust recent voltage observations rather than one potentially noisy sample.

MVP objective:

```text
objective = median(valid_bpv_voltage_mv over evaluation samples)^2
```

Reason:
- fixed load means voltage-squared is order-equivalent to electrical power
- median reduces sensitivity to a single transient sample
- firmware still does not duplicate calibrated backend power calculations

Comparison with deadband:

```text
relative_change = (new_objective - previous_objective) / max(abs(previous_objective), epsilon)

if relative_change > deadband:
    improved
elif relative_change < -deadband:
    worsened
else:
    unchanged/hold-direction policy
```

The exact unchanged policy is deterministic and host-tested: keep the current direction for one more perturbation unless at a bound, where reverse.

---

## Mixer Rule During Adaptive Mode

Mixer remains a separate safety/rule actuator. Phase 6 does not infer a biological optimum for mixing.

MVP options implemented as configuration:

```text
mixer_policy = off | periodic
```

`periodic` requests mixer ON for a short configured duration at a configured interval, but the existing max-runtime/cooldown safety remains authoritative. No sensor-derived optimization claim is attached to mixing.

---

## Module Map

### Module 6.1: Host-Testable P&O Optimizer Core
Plan: `docs/superpowers/plans/phase_6/phase_6_1.md`

Produces:
- optimizer config validation
- deterministic P&O state machine
- median objective window
- deadband/boundary behavior
- reset/hold semantics
- extensive native tests

### Module 6.2: ESP32 Adaptive Runtime Integration
Plan: `docs/superpowers/plans/phase_6/phase_6_2.md`

Produces:
- Adaptive ControlTask integration
- optimizer-direction telemetry
- adaptive config command handling
- local offline continuation
- manual/safe-stop preemption
- periodic mixer policy integration

### Module 6.3: Backend Adaptive Experiment Orchestration and PWA UX
Plan: `docs/superpowers/plans/phase_6/phase_6_3.md`

Produces:
- adaptive experiment configuration persistence
- command contract extension/config delivery
- start validation
- Adaptive experiment form/review UI
- live optimizer-state visualization without fabricated gain

### Module 6.4: Adaptive HIL and Acceptance
Plan: `docs/superpowers/plans/phase_6/phase_6_4.md`

Produces:
- deterministic simulator adaptive behavior for integration tests
- objective-direction tests
- bound/fault/network/preemption HIL
- long adaptive smoke
- full Phase 6 regression gate

---

## Product Design Requirements

Adaptive mode must not look like autonomous magic. The operator should be able to see:
- current mode
- current confirmed PWM
- optimizer direction
- whether optimizer is `initializing`, `perturbing`, `settling`, `holding`, or `suspended`
- last valid BPV observation age
- configured PWM bounds/step/settling time
- why optimization is held, if held

Starting Adaptive mode requires a review screen that states what the controller is allowed to change and what it cannot change.

Manual override requires an explicit mode transition out of Adaptive. The UI must not present simultaneous Manual and Adaptive ownership of the same LED actuator.

## Data Analytics Boundary

Phase 6 telemetry may expose control-state context needed for later analysis, but it must not calculate a headline gain.

Allowed control diagnostics:

```text
mode
optimizer_direction
current PWM
optional optimizer state/hold reason through processed backend status if protocol is extended intentionally
```

Not allowed as optimizer claims:

```text
energy gain %
CO2 improvement %
biomass improvement %
```

Those require completed experiment analysis in Phase 7.

## Planned Commit Sequence

1. `feat: add BioVolt perturb and observe optimizer core`
2. `feat: integrate adaptive controller on ESP32`
3. `feat: orchestrate BioVolt Adaptive experiments`
4. `test: validate BioVolt adaptive control on hardware`

## Phase 6 Exit Criteria

- [ ] P&O core is host-testable without Arduino dependencies.
- [ ] Optimizer uses a robust voltage-squared objective and fixed-load equivalence is documented.
- [ ] PWM never leaves safety/config bounds.
- [ ] Settling window prevents immediate pre-change comparisons.
- [ ] Invalid BPV data suspends perturbation rather than substituting zero.
- [ ] Direction reverses when objective worsens beyond deadband.
- [ ] Bound behavior is deterministic and tested.
- [ ] Manual and Safe Stop preempt Adaptive control.
- [ ] ESP32 reboot returns to Monitor-safe, not auto-resumed Adaptive.
- [ ] Network loss does not break local hardware safety.
- [ ] Mixer remains rule/cooldown controlled and outside P&O optimization.
- [ ] Adaptive configuration is persisted with experiment provenance.
- [ ] UI exposes optimizer state/constraints but no fabricated improvement metric.
- [ ] Existing Phase 0 to 5 regression suites remain green.

## Handoff to Phase 7

Phase 7 turns persisted Passive and Adaptive experiment observations into explicit, quality-gated A/B metrics, trend charts, exports, and judge-facing scientific summaries.
