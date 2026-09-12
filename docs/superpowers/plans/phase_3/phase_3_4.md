# Phase 3.4: Actuator Drivers and Phase 3 Safety Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement grow-light and mixer outputs with deterministic safe boot behavior, bounded PWM, mixer runtime/cooldown protection, and no adaptive-control claim.

**Architecture:** Hardware-specific sinks are kept separate from pure safety policy. `SafetyPolicy` is host-testable; `ActuatorController` applies permitted commands to ESP32 GPIO/LEDC. Phase 3 remains `monitor` mode by default and publishes the actual applied actuator state.

**Tech Stack:** ESP32 LEDC PWM, GPIO, C++17, PlatformIO Unity native tests.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Grow LED and mixer GPIOs are logic-only outputs into suitable driver stages.
- Boot and reset behavior must drive grow LED PWM to 0 and mixer OFF before higher-level initialization.
- Requested PWM is clamped to configured `[ledPwmMin, ledPwmMax]`.
- Mixer cannot remain ON longer than `mixerMaxRuntimeS`.
- A new mixer activation is rejected during `mixerCooldownS` after an automatic/off transition.
- Phase 3 does not execute Perturb & Observe.
- `optimizerDirection` remains 0.
- Safety rules override all future command/control requests.

---

### Task 1: Implement host-testable safety policy

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/SafetyPolicy.h`
- Create: `firmware/esp32/test/test_core_safety/test_main.cpp`

**Interfaces:**

```cpp
struct SafetyLimits {
  uint8_t pwmMin{0};
  uint8_t pwmMax{255};
  uint32_t mixerMaxRuntimeMs{10000};
  uint32_t mixerCooldownMs{60000};
};

class SafetyPolicy {
 public:
  explicit SafetyPolicy(SafetyLimits limits);
  uint8_t clampPwm(int requested) const;
  bool canStartMixer(uint64_t nowMs) const;
  void noteMixerStarted(uint64_t nowMs);
  bool mixerMustStop(uint64_t nowMs) const;
  void noteMixerStopped(uint64_t nowMs);
};
```

- [ ] **Step 1: Write failing PWM clamp tests**

Cover requests below min, inside range, and above max.

- [ ] **Step 2: Write mixer runtime/cooldown tests**

Example:

```text
start at t=1000 ms
max runtime=10000 ms
mustStop false at 10999
mustStop true at 11000
stop at 11000
canStart false until 71000
canStart true at 71000
```

- [ ] **Step 3: Implement policy**

Use 64-bit monotonic times passed by caller. No Arduino calls.

- [ ] **Step 4: Run native tests**

```bash
pio test -e native -f test_core_safety
```

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/lib/BioVoltCore/SafetyPolicy.h firmware/esp32/test/test_core_safety
git commit -m "feat: add BioVolt actuator safety policy"
```

---

### Task 2: Implement grow-light PWM driver

**Files:**
- Create: `firmware/esp32/src/actuators/GrowLightDriver.h`
- Create: `firmware/esp32/src/actuators/GrowLightDriver.cpp`

**Interfaces:**

```cpp
class GrowLightDriver {
 public:
  void begin();
  void write(uint8_t pwm);
  uint8_t appliedPwm() const;
};
```

- [ ] **Step 1: Configure LEDC**

Use 8-bit duty and a 5 kHz channel. Set duty `0` before attaching/enabling the external load stage.

- [ ] **Step 2: Keep applied state**

`appliedPwm()` reports what was actually written to LEDC.

- [ ] **Step 3: Build firmware**

```bash
pio run -e esp32dev
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/src/actuators/GrowLightDriver.*
git commit -m "feat: drive BioVolt grow-light PWM safely"
```

---

### Task 3: Implement mixer driver

**Files:**
- Create: `firmware/esp32/src/actuators/MixerDriver.h`
- Create: `firmware/esp32/src/actuators/MixerDriver.cpp`

**Interfaces:**

```cpp
class MixerDriver {
 public:
  void begin();
  void write(bool on);
  bool isOn() const;
};
```

- [ ] **Step 1: Ensure OFF-before-output initialization**

Write LOW before configuring/activating the driver output so reset does not create a transient ON pulse.

- [ ] **Step 2: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/actuators/MixerDriver.*
git commit -m "feat: drive BioVolt mixer output safely"
```

---

### Task 4: Implement `ActuatorController`

**Files:**
- Create: `firmware/esp32/src/actuators/ActuatorController.h`
- Create: `firmware/esp32/src/actuators/ActuatorController.cpp`

**Interfaces:**

```cpp
struct ActuatorRequest {
  int growLedPwm{0};
  bool mixerOn{false};
};

class ActuatorController {
 public:
  ActuatorController(GrowLightDriver&, MixerDriver&, SafetyPolicy&);
  void begin();
  ActuatorState apply(const ActuatorRequest& request, uint64_t nowMs);
  ActuatorState enforceTimeouts(uint64_t nowMs);
  ActuatorState state() const;
};
```

- [ ] **Step 1: Apply PWM through safety clamp**

Never write raw requested PWM directly to hardware.

- [ ] **Step 2: Enforce mixer start permission**

A denied start request leaves mixer OFF.

- [ ] **Step 3: Enforce runtime timeout even without new request**

`enforceTimeouts()` turns mixer OFF when maximum runtime expires.

- [ ] **Step 4: Build and bench-test with load disconnected**

First verify GPIO/PWM behavior with LED/motor power stage disconnected or safely instrumented.

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/src/actuators
git commit -m "feat: enforce BioVolt actuator safety at hardware boundary"
```

---

### Task 5: Define Phase 3 control baseline

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/ControlBaseline.h`
- Create: `firmware/esp32/test/test_control_baseline/test_main.cpp`

**Interfaces:**

```cpp
ControlState phase3ControlState();
ActuatorRequest phase3DefaultActuatorRequest();
```

Expected:

```text
mode = Monitor
optimizerDirection = 0
PWM = 0
mixer = false
```

- [ ] **Step 1: Write failing baseline test**
- [ ] **Step 2: Implement constants/functions**
- [ ] **Step 3: Run native tests**

```bash
pio test -e native -f test_control_baseline
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/lib/BioVoltCore/ControlBaseline.h firmware/esp32/test/test_control_baseline
git commit -m "feat: define non-adaptive Phase 3 control baseline"
```

## Module 3.4 Exit Criteria

- [ ] Hardware outputs boot safe.
- [ ] PWM is always clamped through safety policy.
- [ ] Mixer max runtime and cooldown are independently tested.
- [ ] Mixer timeout is enforced without requiring a new external command.
- [ ] Phase 3 mode is Monitor and optimizer direction is zero.
- [ ] No P&O implementation or adaptive-performance claim exists.
