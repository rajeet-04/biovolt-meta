# Phase 3.5: FreeRTOS Runtime, Shared State, and Task Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run sensing, control, actuator application, and networking as isolated FreeRTOS responsibilities so temporary network stalls cannot stop hardware acquisition or safety enforcement.

**Architecture:** `RuntimeStateStore` owns the latest coherent sensor/control/actuator snapshot behind a mutex. `SensorTask` samples at 500 ms using `vTaskDelayUntil`. `ControlTask` runs the Phase 3 non-adaptive baseline and writes a one-slot actuator request queue. `ActuatorTask` applies queued requests and independently enforces mixer timeouts. Networking arrives in Module 3.6 as a separate task consuming snapshots.

**Tech Stack:** ESP32 FreeRTOS, queues, mutexes, `esp_timer_get_time()`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- No task may hold the runtime-state mutex while doing I2C, GPIO, serial, or network I/O.
- Sensor cadence target is 500 ms.
- Use `vTaskDelayUntil`, not repeated `delay(500)`.
- Control cadence target is 500 ms.
- Actuator timeout enforcement runs at least every 100 ms.
- Task communication uses snapshots and queues, not mutable global structs.
- Phase 3 control output remains Monitor mode, optimizer direction 0.

---

### Task 1: Implement thread-safe runtime state store

**Files:**
- Create: `firmware/esp32/src/runtime/RuntimeStateStore.h`
- Create: `firmware/esp32/src/runtime/RuntimeStateStore.cpp`

**Interfaces:**

```cpp
struct RuntimeSnapshot {
  SensorFrame sensors;
  ActuatorState actuators;
  ControlState control;
  uint64_t sampledAtMs{0};
};

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

Return false when mutex allocation fails so startup can fail safely.

- [ ] **Step 2: Keep lock scopes copy-only**

Acquire mutex, copy struct, release immediately.

- [ ] **Step 3: Build firmware**

```bash
pio run -e esp32dev
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/src/runtime/RuntimeStateStore.*
git commit -m "feat: add thread-safe BioVolt runtime state store"
```

---

### Task 2: Implement SensorTask with drift-resistant 500 ms schedule

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

- [ ] **Step 1: Use `TickType_t lastWake = xTaskGetTickCount()`**

Loop:

```cpp
for (;;) {
  const uint64_t nowMs = esp_timer_get_time() / 1000ULL;
  auto frame = ctx->sensors->sample(nowMs);
  ctx->state->updateSensors(frame, nowMs);
  vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
}
```

- [ ] **Step 2: Add serial cadence diagnostic behind compile flag**

When `BIOVOLT_DEBUG_TASK_TIMING` is defined, print measured loop deltas once every 20 cycles, not every sample.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/runtime/SensorTask.*
git commit -m "feat: sample BioVolt sensors on a 500 ms FreeRTOS task"
```

---

### Task 3: Implement one-slot actuator request queue and ControlTask

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

- [ ] **Step 1: Allocate queue length 1 for `ActuatorRequest`**

Use `xQueueCreate(1, sizeof(ActuatorRequest))`.

- [ ] **Step 2: Run at 500 ms**

Each cycle:

```text
build phase3 control state
update runtime control state
build safe default actuator request
xQueueOverwrite latest request
```

- [ ] **Step 3: Explicitly set optimizer direction to zero**

Do not create a placeholder optimizer function.

- [ ] **Step 4: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/runtime/ControlTask.*
git commit -m "feat: run BioVolt control baseline in isolated FreeRTOS task"
```

---

### Task 4: Implement ActuatorTask

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

- [ ] **Step 1: Poll queue with maximum 100 ms wait**

If request arrives, apply it. If no request arrives, still call `enforceTimeouts(nowMs)`.

- [ ] **Step 2: Update runtime state with actual applied outputs**

Never publish requested state when safety policy rejected/clamped it.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/runtime/ActuatorTask.*
git commit -m "feat: isolate BioVolt actuator application and timeout enforcement"
```

---

### Task 5: Wire task startup in `main.cpp`

**Files:**
- Modify: `firmware/esp32/src/main.cpp`

Recommended priorities/stacks:

```text
SensorTask    priority 3, stack 4096
ControlTask   priority 3, stack 3072
ActuatorTask  priority 3, stack 3072
```

Pin application hardware tasks to core 1. Keep Wi-Fi/network task creation for Module 3.6.

- [ ] **Step 1: Initialize state, sensors, actuators, queue before starting tasks**

If mandatory runtime primitives fail, keep outputs safe and do not start partially initialized actuator tasks.

- [ ] **Step 2: Create tasks with checked return codes**

Print task name on failure and remain in safe degraded mode.

- [ ] **Step 3: Make Arduino `loop()` idle**

```cpp
void loop() {
  vTaskDelay(pdMS_TO_TICKS(1000));
}
```

- [ ] **Step 4: Upload and inspect timing for at least 5 minutes**

Sensor timing should remain close to 500 ms without cumulative drift.

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/src/main.cpp firmware/esp32/src/runtime
git commit -m "feat: run BioVolt hardware responsibilities as FreeRTOS tasks"
```

## Module 3.5 Exit Criteria

- [ ] Sensor/control/actuator responsibilities are isolated.
- [ ] Runtime-state lock never wraps physical/network I/O.
- [ ] Sensor/control schedules use `vTaskDelayUntil`.
- [ ] Actuator timeout enforcement continues even if ControlTask has no new request.
- [ ] Published actuator state is actual applied state.
- [ ] Arduino `loop()` contains no application logic.
