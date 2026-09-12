# Phase 6.2: ESP32 Adaptive Runtime Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the tested P&O core into the ESP32 runtime so Adaptive mode can safely own grow-light PWM while preserving command preemption, telemetry, local safety, and offline operation.

**Architecture:** `ControlTask` selects one control policy by confirmed mode: Monitor, Passive, Manual, or Adaptive. Adaptive mode owns a `PAndOOptimizer` instance and sends its requested PWM through the same one-slot actuator queue already used by non-adaptive modes. `CommandTask` owns mode/config changes and resets optimizer state on every ownership transition.

**Tech Stack:** Existing ESP32 PlatformIO/FreeRTOS firmware, BioVoltCore optimizer, RuntimeStateStore, ActuatorController, command/ack path.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- One owner controls grow LED at a time.
- Adaptive requests never bypass `SafetyPolicy` or `ActuatorTask`.
- Transition out of Adaptive disables/resets optimizer before another mode writes PWM.
- Safe Stop has highest priority.
- Adaptive config is held in RAM for the current experiment, not persisted as auto-resume NVS state.
- Network disconnect does not stop an already-configured Adaptive loop.
- Reboot returns Monitor/PWM 0/mixer off.
- `optimizer_direction` telemetry equals current optimizer direction `-1/0/+1`.
- Invalid BPV sensor health suspends optimizer.
- Mixer rule requests still pass existing cooldown/runtime enforcement.

---

### Task 1: Extend runtime control state for adaptive diagnostics

**Files:**
- Modify: `firmware/esp32/lib/BioVoltCore/RuntimeTypes.h`
- Modify: `firmware/esp32/src/runtime/RuntimeStateStore.h`
- Create: `firmware/esp32/test/test_adaptive_runtime_types/test_main.cpp`

Add:

```cpp
enum class OptimizerRuntimeState {
  Inactive,
  Initialize,
  Settle,
  Observe,
  Hold,
};

struct ControlState {
  ControlMode mode{ControlMode::Monitor};
  int8_t optimizerDirection{0};
  OptimizerRuntimeState optimizerState{OptimizerRuntimeState::Inactive};
  uint8_t adaptiveTargetPwm{0};
  bool optimizerSuspended{false};
  HoldReason holdReason{HoldReason::None};
};
```

Raw telemetry contract need not expose all new fields. `optimizerDirection` remains required raw field. Additional diagnostics may travel through a later processed status endpoint instead of changing raw schema.

- [ ] **Step 1: Write safe-default test**
- [ ] **Step 2: Implement POD-safe runtime types**
- [ ] **Step 3: Build native/ESP32 targets**
- [ ] **Step 4: Commit**

```bash
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
git add firmware/esp32/lib/BioVoltCore/RuntimeTypes.h firmware/esp32/src/runtime/RuntimeStateStore.h firmware/esp32/test/test_adaptive_runtime_types
git commit -m "feat: expose BioVolt adaptive runtime state"
```

---

### Task 2: Extend command model for adaptive configuration

**Files:**
- Modify: `shared/schemas/device-command.v1.schema.json`
- Modify: `docs/protocols/device-command-protocol.md`
- Modify: `firmware/esp32/lib/BioVoltCore/CommandModel.h`
- Modify: `firmware/esp32/lib/BioVoltCore/CommandParser.cpp`
- Modify: `firmware/esp32/test/test_command_parser/test_main.cpp`

Preferred approach: extend `set_mode` payload when `mode=adaptive` with a strict `adaptive_config` object rather than introducing arbitrary free-form config commands.

Example:

```json
{
  "mode": "adaptive",
  "adaptive_config": {
    "initial_pwm": 64,
    "pwm_min": 20,
    "pwm_max": 180,
    "pwm_step": 4,
    "settle_ms": 3000,
    "minimum_valid_samples": 3,
    "objective_deadband_fraction": 0.01,
    "mixer_policy": "off"
  }
}
```

- [ ] **Step 1: Update shared contract tests for strict adaptive config**
- [ ] **Step 2: Keep config absent for non-adaptive modes**
- [ ] **Step 3: Parse into fixed-size/POD queue representation**
- [ ] **Step 4: Validate with same bounds as optimizer validator**
- [ ] **Step 5: Run shared/native tests and commit**

```bash
pytest shared/tests -v
pio test -d firmware/esp32 -e native -f test_command_parser
git add shared/schemas/device-command.v1.schema.json docs/protocols/device-command-protocol.md firmware/esp32/lib/BioVoltCore/CommandModel.h firmware/esp32/lib/BioVoltCore/CommandParser.cpp firmware/esp32/test/test_command_parser/test_main.cpp
git commit -m "feat: configure BioVolt adaptive mode through device command"
```

---

### Task 3: Enable Adaptive policy in CommandTask

**Files:**
- Modify: `firmware/esp32/lib/BioVoltCore/CommandPolicy.h`
- Modify: `firmware/esp32/test/test_command_policy/test_main.cpp`
- Modify: `firmware/esp32/src/runtime/CommandTask.cpp`

Rules:
- valid `set_mode adaptive` is now allowed
- missing/invalid adaptive config rejects `invalid_payload`
- entering Adaptive resets optimizer and stores current experiment config in runtime controller context
- leaving Adaptive disables optimizer before acknowledging new mode applied
- `set_led_pwm` in Adaptive is rejected with a deterministic reason such as `mode_owned_by_optimizer`
- Safe Stop remains allowed

If adding a new reason code, update `device-ack.v1` schema first.

- [ ] **Step 1: Update policy tests for Adaptive ownership**
- [ ] **Step 2: Add manual LED write rejection while Adaptive test**
- [ ] **Step 3: Implement transition/reset semantics**
- [ ] **Step 4: Ensure ack `applied_state.mode=adaptive` only after config accepted**
- [ ] **Step 5: Run native/build and commit**

```bash
pio test -d firmware/esp32 -e native -f test_command_policy
pio run -d firmware/esp32 -e esp32dev
git add firmware/esp32/lib/BioVoltCore/CommandPolicy.h firmware/esp32/test/test_command_policy/test_main.cpp firmware/esp32/src/runtime/CommandTask.cpp shared/schemas/device-ack.v1.schema.json
git commit -m "feat: allow safe BioVolt Adaptive mode ownership"
```

---

### Task 4: Integrate optimizer into ControlTask

**Files:**
- Modify: `firmware/esp32/src/runtime/ControlTask.h`
- Modify: `firmware/esp32/src/runtime/ControlTask.cpp`
- Create: `firmware/esp32/src/runtime/AdaptiveController.h`
- Create: `firmware/esp32/src/runtime/AdaptiveController.cpp`

**Interfaces:**

```cpp
class AdaptiveController {
 public:
  bool enable(const PAndOConfig& config, uint64_t nowMs);
  void disable();
  ActuatorRequest update(const SensorFrame& sensors, uint64_t nowMs);
  ControlState state() const;
};
```

`ControlTask` selection:

```text
Monitor  -> LED 0/mixer off default
Passive  -> fixed experiment setpoints
Manual   -> last acknowledged manual requested state
Adaptive -> AdaptiveController update
```

- [ ] **Step 1: Ensure Adaptive reads latest sensor snapshot outside mutex-protected hardware I/O**
- [ ] **Step 2: Feed BPV validity from ADS health + voltage validity**
- [ ] **Step 3: Queue optimizer PWM only when optimizer produces a new request**
- [ ] **Step 4: Publish optimizer state/direction every control cycle**
- [ ] **Step 5: Build and commit**

```bash
pio run -d firmware/esp32 -e esp32dev
git add firmware/esp32/src/runtime/ControlTask.* firmware/esp32/src/runtime/AdaptiveController.*
git commit -m "feat: run BioVolt adaptive optimizer in ControlTask"
```

---

### Task 5: Add periodic mixer policy without optimizer coupling

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/MixerPolicy.h`
- Create: `firmware/esp32/test/test_mixer_policy/test_main.cpp`
- Modify: `firmware/esp32/src/runtime/AdaptiveController.cpp`

Config:

```text
policy = off | periodic
period_ms
requested_on_ms
```

Rules:
- policy generates a mixer request schedule only
- ActuatorController safety may shorten/reject it
- optimizer objective/direction never depends on mixer success in Phase 6
- mixer events can be visible through normal actuator telemetry

- [ ] **Step 1: Write off policy test**
- [ ] **Step 2: Write periodic due/not-due tests**
- [ ] **Step 3: Write no catch-up burst after long delay test**
- [ ] **Step 4: Implement policy and integrate request**
- [ ] **Step 5: Run and commit**

```bash
pio test -d firmware/esp32 -e native -f test_mixer_policy
pio run -d firmware/esp32 -e esp32dev
git add firmware/esp32/lib/BioVoltCore/MixerPolicy.h firmware/esp32/test/test_mixer_policy firmware/esp32/src/runtime/AdaptiveController.cpp
git commit -m "feat: add independent periodic mixer policy for Adaptive mode"
```

---

### Task 6: Verify preemption, reboot, and offline continuation

**Files:**
- Create: `firmware/esp32/test/test_adaptive_preemption/test_main.cpp`
- Modify: `firmware/esp32/README.md`

Tests/HIL assertions:
- Safe Stop disables optimizer before PWM 0 applied
- switching Manual disables optimizer
- Wi-Fi status has no direct effect on optimizer update path
- reboot setup initializes Monitor-safe state
- stale/invalid voltage causes Hold

- [ ] **Step 1: Add host-testable ownership/preemption tests where possible**
- [ ] **Step 2: Add firmware boot assertion/log line for Monitor-safe state**
- [ ] **Step 3: Document network-loss local-continuation policy**
- [ ] **Step 4: Run full native/build and commit**

```bash
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
git add firmware/esp32/test/test_adaptive_preemption firmware/esp32/README.md
git commit -m "test: verify BioVolt adaptive ownership and fail-safe behavior"
```

## Module 6.2 Exit Criteria

- [ ] Adaptive config enters firmware through versioned command schema.
- [ ] One control owner exists per actuator.
- [ ] Adaptive PWM goes through existing actuator safety.
- [ ] Manual LED writes are rejected while optimizer owns LED.
- [ ] Safe Stop preempts Adaptive immediately.
- [ ] Wi-Fi loss does not stop local optimizer or safety.
- [ ] Reboot cannot auto-resume Adaptive.
- [ ] Mixer policy remains independent of P&O objective.
