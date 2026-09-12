# Phase 6.4: Adaptive Hardware-in-the-Loop and Acceptance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove Adaptive mode behaves safely and predictably on the real ESP32 under changing BPV signal, actuator bounds, sensor faults, network loss, and operator preemption before any experiment comparison is presented to judges.

**Architecture:** Acceptance combines deterministic simulator behavior for CI, host-level optimizer traces, and real-device HIL. The real reactor test records control behavior and telemetry but does not assume the biological system must show a specific improvement during the acceptance run.

**Tech Stack:** Python simulator, FastAPI integration tests, PlatformIO native tests, real ESP32, Docker Compose, PWA acceptance checks.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Synthetic optimizer response curves are test fixtures only and are visibly labeled synthetic.
- HIL pass criteria focus on control safety/correctness, not guaranteed BPV gain.
- No adaptive experiment acceptance invents a result if BPV response is flat or noisy.
- Safe Stop and fault behavior are mandatory pass gates.

---

### Task 1: Add deterministic simulator Adaptive parity

**Files:**
- Modify: `simulator/src/biovolt_simulator/commands.py`
- Create: `simulator/src/biovolt_simulator/adaptive.py`
- Create: `simulator/tests/test_adaptive.py`

Simulator behavior:
- accepts valid Adaptive config
- produces deterministic PWM/direction evolution against an explicitly synthetic response function
- uses same command/ack semantics
- telemetry remains source-neutral and schema-compatible

- [ ] **Step 1: Write adaptive config accept/reject tests**
- [ ] **Step 2: Write deterministic direction-change trace test**
- [ ] **Step 3: Ensure simulator output is documented as synthetic test behavior**
- [ ] **Step 4: Run and commit**

```bash
pytest simulator/tests/test_adaptive.py -v
git add simulator/src/biovolt_simulator simulator/tests/test_adaptive.py
git commit -m "test: add synthetic BioVolt Adaptive simulator parity"
```

---

### Task 2: Add backend/PWA Adaptive integration tests

**Files:**
- Create: `backend/tests/integration/test_adaptive_control_lifecycle.py`
- Create: `frontend/tests/integration/adaptiveControlStatus.test.tsx`

Backend assertions:
- adaptive config command delivered
- experiment becomes running only after applied ack
- telemetry accepts optimizer direction -1/0/+1
- safe stop completes experiment

Frontend assertions:
- Adaptive ownership visible
- manual LED control unavailable
- stale telemetry warning visible
- no `% gain` card on live Adaptive control panel

- [ ] **Step 1: Implement backend lifecycle test**
- [ ] **Step 2: Implement PWA state test**
- [ ] **Step 3: Run and commit**

```bash
cd backend && pytest tests/integration/test_adaptive_control_lifecycle.py -v
cd ../frontend && npm test -- adaptiveControlStatus && npm run typecheck
git add backend/tests/integration/test_adaptive_control_lifecycle.py frontend/tests/integration/adaptiveControlStatus.test.tsx
git commit -m "test: verify BioVolt Adaptive control integration"
```

---

### Task 3: Add real ESP32 Adaptive HIL checklist

**Files:**
- Create: `scripts/phase6_adaptive_hil.md`

Procedure:

```text
1. Stop simulator and connect real ESP32.
2. Verify Monitor boot state, PWM 0, mixer OFF.
3. Start a calibrated Adaptive experiment with conservative PWM bounds.
4. Verify applied ack and mode=adaptive.
5. Record initial PWM and optimizer direction.
6. Observe at least several complete perturb/settle/observe cycles.
7. Verify requested/applied PWM remains within bounds.
8. Cover upper/lower bound behavior if safe to do so with chosen test envelope.
9. Verify invalid BPV input causes Hold rather than PWM runaway.
10. Restore sensor and verify controlled recovery.
11. Interrupt backend/network while ESP32 remains powered.
12. Verify local optimizer/safety continue according to policy.
13. Restore network and verify live telemetry reconnect.
14. Issue Safe Stop and verify Monitor/PWM 0/mixer OFF.
```

Record:

```text
telemetry sequence
uptime
BPV voltage
PWM
optimizer direction
mode
network state
hold/fault observation
```

- [ ] **Step 1: Add pre-power safe PWM envelope requirement**
- [ ] **Step 2: Add evidence table and failure conditions**
- [ ] **Step 3: Execute on real hardware**
- [ ] **Step 4: Record actual observed behavior in PR/release evidence**
- [ ] **Step 5: Commit checklist**

```bash
git add scripts/phase6_adaptive_hil.md
git commit -m "docs: add BioVolt Adaptive hardware acceptance"
```

---

### Task 4: Verify operator preemption and ownership transitions

**Files:**
- Modify: `scripts/phase6_adaptive_hil.md`

Scenarios:

```text
Adaptive -> Safe Stop
Adaptive -> Manual mode through acknowledged command
Adaptive -> Monitor
```

For every scenario:
- optimizer direction becomes 0 after ownership leaves Adaptive
- no late optimizer PWM write overrides the new mode
- actual telemetry state matches the terminal command acknowledgement

- [ ] **Step 1: Execute ownership transition matrix**
- [ ] **Step 2: Verify no race reasserts old Adaptive PWM after Safe Stop**
- [ ] **Step 3: Mark any race as Phase 6 blocker**

---

### Task 5: Execute extended Adaptive smoke

Minimum target:

```text
30 minutes real device
```

During smoke:
- Adaptive active for a significant interval
- at least one backend/network interruption
- no ESP32 reset
- no progressive heap collapse
- PWM bounded
- sensor faults do not cause unsafe output
- telemetry resumes after network restoration

This smoke is not the A/B experiment itself. It validates runtime reliability.

- [ ] **Step 1: Record free heap/uptime/sequence periodically**
- [ ] **Step 2: Verify no runaway perturb rate**
- [ ] **Step 3: Verify actuator safety remains authoritative throughout**

---

### Task 6: Phase 6 regression gate

Run:

```bash
pytest shared/tests -v
cd backend && pytest -v
cd ../simulator && pytest -v
cd ../frontend && npm test && npm run typecheck && npm run lint && npm run build
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
```

- [ ] **Step 1: Run all software tests/builds**
- [ ] **Step 2: Complete real ESP32 Adaptive HIL**
- [ ] **Step 3: Confirm live UI contains no fabricated gain metric**
- [ ] **Step 4: Confirm raw device telemetry still contains no backend-derived power/biomass/carbon fields**

## Module 6.4 Exit Criteria

- [ ] Adaptive mode passes deterministic CI and real HIL.
- [ ] PWM remains bounded under normal, noisy, bound, and sensor-fault scenarios.
- [ ] Network loss does not break local safety/control policy.
- [ ] Safe Stop reliably ends Adaptive ownership with no late override.
- [ ] Extended smoke has no unexpected reboot/runaway behavior.
- [ ] No Phase 6 acceptance criterion requires a fabricated biological improvement.
- [ ] Full Phase 0 to 6 regression passes before analytics work begins.
