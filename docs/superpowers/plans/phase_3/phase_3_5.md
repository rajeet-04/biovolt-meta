# Phase 3.5: FreeRTOS Runtime, Shared State, Task Isolation, and Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run sensing, control, actuator application, and serial provisioning as isolated FreeRTOS responsibilities so network or serial activity cannot stop hardware acquisition or safety enforcement.

**Architecture:** Shared `RuntimeSnapshot` DTOs live in `lib/BioVoltCore/RuntimeTypes.h` so telemetry serialization can be tested natively. `RuntimeStateStore` owns the latest coherent sensor/control/actuator snapshot behind a mutex. SensorTask and ControlTask use drift-resistant 500 ms schedules. ActuatorTask consumes a one-slot latest-request queue and enforces timeouts independently. ProvisioningTask keeps the serial CLI available after Arduino `loop()` becomes idle. Network/TelemetryTask is added in Module 3.6.

**Tech Stack:** ESP32 FreeRTOS, queues, mutexes, `esp_timer_get_time()`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- No task holds the runtime-state mutex while doing I2C, GPIO, serial, or network I/O.
- Sensor cadence target is 500 ms using `vTaskDelayUntil`.
- Control cadence target is 500 ms using `vTaskDelayUntil`.
- Actuator timeout enforcement runs at least every 100 ms.
- Task communication uses copied snapshots and queues, not mutable cross-task globals.
- Phase 3 control remains `monitor`, optimizer direction `0`, PWM `0`, mixer OFF.
- Active `RuntimeConfig` is immutable for the boot session.
- Provisioning edits/saves only a draft configuration and requires reboot to apply.
- Arduino `loop()` contains no application logic after tasks start.

---

### Task 1: Move RuntimeSnapshot into the native-testable core

**Files:**
- Modify: `firmware/esp32/lib/BioVoltCore/RuntimeTypes.h`
- Modify: `firmware/esp32/test/test_core_types/test_main.cpp`

**Interfaces:**

```cpp
struct ActuatorState {
  uint8_t growLedPwm{0};
  bool mixerOn{false};
};

enum class ControlMode { Monitor, Passive, Adaptive, Manual };

struct ControlState {
  ControlMode mode{ControlMode::Monitor};
  int8_t optimizerDirection{0};
};

struct RuntimeSnapshot {
  SensorFrame sensors;
  ActuatorState actuators;
  ControlState control;
  uint64_t sampledAtMs{0};
};
```

- [ ] **Step 1: Add failing default-state test**

Assert a new RuntimeSnapshot has invalid/default sensor frame, PWM 0, mixer false, Monitor mode, and optimizer direction 0.

- [ ] **Step 2: Implement DTOs without Arduino dependencies**

- [ ] **Step 3: Run native tests**

```bash
cd firmware/esp32
pio test -e native -f test_core_types
```

- [ ] **Step 4: Commit**

```bash
git add lib/BioVoltCore/RuntimeTypes.h test/test_core_types
git commit -m "feat: define native-testable BioVolt runtime snapshot"
```

---

### Task 2: Implement thread-safe RuntimeStateStore

**Files:**
- Create: `firmware/esp32/src/runtime/RuntimeStateStore.h`
- Create: `firmware/esp32/src/runtime/RuntimeStateStore.cpp`

**Interfaces:**

```cpp
class RuntimeStateStore {
 public:
  bool begin();
  void updateSensors(const SensorFrame& frame, uint64_t sampledAtMs);
  void updateActuators(const ActuatorState& state);
  void updateControl(const ControlState& state);
  RuntimeSnapshot snapshot();
};
```

- [ ] **Step 1: Create mutex in `begin()`**

Return false if allocation fails so startup can remain safe/degraded.

- [ ] **Step 2: Keep critical sections copy-only**

Acquire mutex, copy/replace small structs, release immediately. Do not call drivers while locked.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add src/runtime/RuntimeStateStore.*
git commit -m "feat: add thread-safe BioVolt runtime state store"
```

---

### Task 3: Implement SensorTask with drift-resistant schedule

**Files:**
- Create: `firmware/esp32/src/runtime/SensorTask.h`
- Create: `firmware/esp32/src/runtime/SensorTask.cpp`

**Interfaces:**

```cpp
struct SensorTaskContext {
  SensorManager* sensors;
  RuntimeStateStore* state;
};

void sensorTaskEntry(void* context);
```

- [ ] **Step 1: Use `vTaskDelayUntil`**

```cpp
TickType_t lastWake = xTaskGetTickCount();
for (;;) {
  const uint64_t nowMs = esp_timer_get_time() / 1000ULL;
  const SensorFrame frame = ctx->sensors->sample(nowMs);
  ctx->state->updateSensors(frame, nowMs);
  vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
}
```

- [ ] **Step 2: Add bounded timing diagnostic**

With `BIOVOLT_DEBUG_TASK_TIMING`, print measured cycle delta once every 20 cycles only.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add src/runtime/SensorTask.*
git commit -m "feat: sample BioVolt sensors on a 500 ms FreeRTOS task"
```

---

### Task 4: Implement one-slot actuator queue and ControlTask

**Files:**
- Create: `firmware/esp32/src/runtime/ControlTask.h`
- Create: `firmware/esp32/src/runtime/ControlTask.cpp`

**Interfaces:**

```cpp
struct ControlTaskContext {
  RuntimeStateStore* state;
  QueueHandle_t actuatorQueue;
};

void controlTaskEntry(void* context);
```

- [ ] **Step 1: Allocate queue length 1**

```cpp
xQueueCreate(1, sizeof(ActuatorRequest));
```

- [ ] **Step 2: Run fixed Phase 3 baseline every 500 ms**

Each cycle:

```text
ControlState = Monitor / optimizer 0
ActuatorRequest = PWM 0 / mixer false
update runtime control state
xQueueOverwrite latest actuator request
```

- [ ] **Step 3: Do not create placeholder optimizer calls**

No P&O interface or fake adaptive branch belongs here.

- [ ] **Step 4: Build and commit**

```bash
pio run -e esp32dev
git add src/runtime/ControlTask.*
git commit -m "feat: run BioVolt control baseline in isolated FreeRTOS task"
```

---

### Task 5: Implement ActuatorTask

**Files:**
- Create: `firmware/esp32/src/runtime/ActuatorTask.h`
- Create: `firmware/esp32/src/runtime/ActuatorTask.cpp`

**Interfaces:**

```cpp
struct ActuatorTaskContext {
  ActuatorController* controller;
  RuntimeStateStore* state;
  QueueHandle_t actuatorQueue;
};

void actuatorTaskEntry(void* context);
```

- [ ] **Step 1: Wait at most 100 ms for request**

On request, apply through ActuatorController. On timeout/no request, still call `enforceTimeouts(nowMs)`.

- [ ] **Step 2: Publish actual applied state**

Never report requested PWM/mixer when safety policy clamped or rejected it.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add src/runtime/ActuatorTask.*
git commit -m "feat: isolate BioVolt actuator application and timeout enforcement"
```

---

### Task 6: Implement low-priority ProvisioningTask

**Files:**
- Create: `firmware/esp32/src/runtime/ProvisioningTask.h`
- Create: `firmware/esp32/src/runtime/ProvisioningTask.cpp`

**Interfaces:**

```cpp
struct ProvisioningTaskContext {
  SerialProvisioner* provisioner;
};

void provisioningTaskEntry(void* context);
```

- [ ] **Step 1: Poll serial provisioner continuously**

```cpp
for (;;) {
  ctx->provisioner->poll();
  vTaskDelay(pdMS_TO_TICKS(20));
}
```

- [ ] **Step 2: Use low priority**

Recommended priority `1`, stack `3072`. Serial provisioning must not preempt sensor/actuator timing unnecessarily.

- [ ] **Step 3: Confirm saved config does not mutate active tasks**

After `config save`, running Wi-Fi/device ID remain unchanged until explicit reboot.

- [ ] **Step 4: Build and commit**

```bash
pio run -e esp32dev
git add src/runtime/ProvisioningTask.*
git commit -m "feat: keep BioVolt serial provisioning available during runtime"
```

---

### Task 7: Wire Phase 3.5 task startup in main.cpp

**Files:**
- Modify: `firmware/esp32/src/main.cpp`

Recommended task allocation:

```text
SensorTask        priority 3, stack 4096, core 1
ControlTask       priority 3, stack 3072, core 1
ActuatorTask      priority 3, stack 3072, core 1
ProvisioningTask  priority 1, stack 3072, core 1 or unpinned
```

TelemetryTask is added separately in Module 3.6.

- [ ] **Step 1: Force hardware outputs safe before task creation**

- [ ] **Step 2: Initialize immutable active config, state store, sensors, actuators, queue, and provisioner**

If config is invalid, do not start network later, but keep safe sensor bench operation and ProvisioningTask available.

- [ ] **Step 3: Create each task with checked return code**

On mandatory hardware-task creation failure, keep outputs safe and print only task name/error.

- [ ] **Step 4: Keep Arduino loop idle**

```cpp
void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
```

- [ ] **Step 5: Upload and inspect 5-minute timing**

Sensor/control schedules should remain near 500 ms without cumulative drift, while `status` and config commands continue working over serial.

- [ ] **Step 6: Commit**

```bash
git add src/main.cpp src/runtime
git commit -m "feat: run BioVolt hardware responsibilities as FreeRTOS tasks"
```

## Module 3.5 Exit Criteria

- [ ] RuntimeSnapshot is native-testable and shared with serializer.
- [ ] Sensor/control/actuator/provisioning responsibilities are isolated.
- [ ] Runtime-state mutex never wraps I/O.
- [ ] Sensor/control use `vTaskDelayUntil`.
- [ ] Actuator timeout enforcement continues without fresh control requests.
- [ ] Provisioning remains usable after application tasks start.
- [ ] Saved draft configuration applies only after reboot.
- [ ] Published actuator state is actual applied state.
- [ ] Arduino `loop()` contains no application logic.
