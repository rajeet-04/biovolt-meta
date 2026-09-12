# Phase 6.1: Host-Testable Perturb & Observe Optimizer Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the entire BioVolt P&O decision algorithm as deterministic, hardware-independent C++ so every state transition, bound, deadband, and invalid-data behavior can be exhaustively tested before it is allowed to control the grow LED.

**Architecture:** `PAndOOptimizer` accepts time-stamped BPV voltage observations and returns a requested PWM only when a perturbation is due. It owns no GPIO, FreeRTOS primitives, WebSocket, calibration, or experiment logic. A small fixed-size observation window calculates a median voltage-squared objective.

**Tech Stack:** C++17, PlatformIO native environment, Unity tests, fixed-size arrays, no dynamic allocation required in optimizer path.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Pure BioVoltCore module, no Arduino headers.
- Objective input is raw/physical BPV voltage in mV from the sensor snapshot.
- Missing/non-finite voltage is invalid, not zero.
- PWM output is integer and bounded.
- Settling time uses supplied monotonic milliseconds.
- Observation window is fixed-capacity.
- No firmware power/current formula.
- No percent gain metric.
- Reset returns state to inactive/initial configuration without actuator side effect.

---

### Task 1: Define optimizer config and validation

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/OptimizerTypes.h`
- Create: `firmware/esp32/lib/BioVoltCore/OptimizerValidation.h`
- Create: `firmware/esp32/test/test_optimizer_validation/test_main.cpp`

**Interfaces:**

```cpp
struct PAndOConfig {
  uint8_t initialPwm{64};
  uint8_t pwmMin{0};
  uint8_t pwmMax{255};
  uint8_t pwmStep{4};
  uint32_t settleMs{3000};
  uint8_t minimumValidSamples{3};
  float objectiveDeadbandFraction{0.01F};
};

ConfigValidationResult validatePAndOConfig(const PAndOConfig& config);
```

Validation:
- min < max
- initial inside bounds
- step > 0
- step <= `(max-min)` and a defined firmware safety maximum, initially 32
- settle >= 500 ms
- min samples 1..9
- deadband finite 0..0.25

- [ ] **Step 1: Write failing boundary tests**
- [ ] **Step 2: Implement pure validator**
- [ ] **Step 3: Run native test**

```bash
pio test -d firmware/esp32 -e native -f test_optimizer_validation
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/lib/BioVoltCore/OptimizerTypes.h firmware/esp32/lib/BioVoltCore/OptimizerValidation.h firmware/esp32/test/test_optimizer_validation
git commit -m "feat: validate BioVolt adaptive optimizer configuration"
```

---

### Task 2: Implement fixed observation window and median objective

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/ObjectiveWindow.h`
- Create: `firmware/esp32/test/test_objective_window/test_main.cpp`

**Interfaces:**

```cpp
class ObjectiveWindow {
 public:
  static constexpr size_t kMaxSamples = 9;
  void clear();
  bool addVoltageMv(float voltageMv);
  size_t validCount() const;
  bool objective(float& voltageSquaredObjective) const;
};
```

Rules:
- reject non-finite sample
- retain up to configured maximum in fixed array
- median of valid voltage values
- objective = median_voltage_mv squared
- calculation uses sufficiently wide floating type to avoid integer overflow

- [ ] **Step 1: Write odd/even median tests**
- [ ] **Step 2: Write outlier test showing median robustness**
- [ ] **Step 3: Write invalid sample does not increase count test**
- [ ] **Step 4: Implement fixed-array median without heap allocation**
- [ ] **Step 5: Run and commit**

```bash
pio test -d firmware/esp32 -e native -f test_objective_window
git add firmware/esp32/lib/BioVoltCore/ObjectiveWindow.h firmware/esp32/test/test_objective_window
git commit -m "feat: calculate robust BioVolt adaptive objective"
```

---

### Task 3: Implement optimizer state machine

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/PAndOOptimizer.h`
- Create: `firmware/esp32/lib/BioVoltCore/PAndOOptimizer.cpp`
- Create: `firmware/esp32/test/test_pando_optimizer/test_main.cpp`

**Interfaces:**

```cpp
enum class OptimizerState {
  Inactive,
  Initialize,
  Settle,
  Observe,
  Hold,
};

struct OptimizerOutput {
  OptimizerState state;
  bool pwmRequestValid{false};
  uint8_t requestedPwm{0};
  int8_t direction{0};
  const char* holdReason{nullptr};
};

class PAndOOptimizer {
 public:
  void enable(const PAndOConfig& config, uint64_t nowMs);
  void disable();
  OptimizerOutput update(uint64_t nowMs, float voltageMv, bool voltageValid);
  OptimizerOutput status() const;
};
```

Deterministic sequence:
1. enable -> request initial PWM, direction +1, enter settle
2. ignore comparison until settle elapsed and enough valid samples collected
3. establish first objective
4. request perturb in current direction
5. settle/collect new window
6. compare objective
7. improved -> keep direction
8. worsened -> reverse direction
9. within deadband -> keep direction once, unless next request hits bound

- [ ] **Step 1: Write enable/initial PWM test**
- [ ] **Step 2: Write settling prevents early perturb test**
- [ ] **Step 3: Write improved keeps direction test**
- [ ] **Step 4: Write worsened reverses direction test**
- [ ] **Step 5: Write deadband unchanged behavior test**
- [ ] **Step 6: Implement state machine**
- [ ] **Step 7: Run and commit**

```bash
pio test -d firmware/esp32 -e native -f test_pando_optimizer
git add firmware/esp32/lib/BioVoltCore/PAndOOptimizer.* firmware/esp32/test/test_pando_optimizer
git commit -m "feat: add BioVolt perturb and observe state machine"
```

---

### Task 4: Implement PWM-bound and invalid-data hold behavior

**Files:**
- Modify: `firmware/esp32/lib/BioVoltCore/PAndOOptimizer.cpp`
- Modify: `firmware/esp32/test/test_pando_optimizer/test_main.cpp`

Rules:
- a proposed step beyond max reverses direction and requests inward bounded step
- same at min
- if valid-sample requirement is not met after settling, enter Hold with `insufficient_valid_data`
- Hold never changes PWM
- valid data recovery clears a fresh objective window before resuming
- long time passage alone must not create multiple catch-up perturbations

- [ ] **Step 1: Write max/min bound tests**
- [ ] **Step 2: Write invalid-data hold test**
- [ ] **Step 3: Write recovery test**
- [ ] **Step 4: Write no catch-up perturbation burst test**
- [ ] **Step 5: Implement behavior**
- [ ] **Step 6: Run and commit**

```bash
pio test -d firmware/esp32 -e native -f test_pando_optimizer
git add firmware/esp32/lib/BioVoltCore/PAndOOptimizer.cpp firmware/esp32/test/test_pando_optimizer/test_main.cpp
git commit -m "feat: hold BioVolt optimizer safely at bounds and sensor faults"
```

---

### Task 5: Add deterministic trace tests

**Files:**
- Create: `firmware/esp32/test/test_optimizer_traces/test_main.cpp`

Synthetic traces:
- monotonic voltage increase with PWM -> continue upward to bound
- unimodal response -> reverse around synthetic optimum
- flat noisy response within deadband -> no rapid direction thrashing
- intermittent invalid samples -> hold/recover

The test is a controller behavior test, not a claim that the real BPV reactor has the synthetic response curve.

- [ ] **Step 1: Implement trace harness with controlled timestamps**
- [ ] **Step 2: Assert bounded number of direction changes on flat noisy trace**
- [ ] **Step 3: Assert final PWM remains within bounds on every trace**
- [ ] **Step 4: Run full native optimizer suite and commit**

```bash
pio test -d firmware/esp32 -e native -f test_optimizer_traces
pio test -d firmware/esp32 -e native
git add firmware/esp32/test/test_optimizer_traces
git commit -m "test: validate BioVolt adaptive optimizer traces"
```

## Module 6.1 Exit Criteria

- [ ] Optimizer core has no hardware/network dependency.
- [ ] Median voltage-squared objective is tested.
- [ ] Settling and sample-window requirements prevent immediate noisy comparisons.
- [ ] Deadband behavior is deterministic.
- [ ] Bounds cannot produce out-of-range requests.
- [ ] Invalid sensor data holds without actuator changes.
- [ ] Synthetic traces test behavior without being represented as biological evidence.
