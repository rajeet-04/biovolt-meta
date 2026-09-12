# Phase 4.4: ESP32 Command Parsing, Safety Application, and Acknowledgement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the real ESP32 receive Phase 4 commands over the existing device WebSocket, validate them, apply only safety-permitted Passive/Manual actions, and send correlated acknowledgements that report actual device state.

**Architecture:** Incoming WebSocket text is parsed into a pure command DTO and placed onto a bounded FreeRTOS command queue. A dedicated `CommandTask` owns command execution and acknowledgement emission. The networking callback never writes GPIO directly. A small command-ID dedupe cache prevents repeated side effects on duplicate delivery.

**Tech Stack:** PlatformIO, ArduinoJson, FreeRTOS queue/task primitives, existing `ActuatorController`, `RuntimeStateStore`, and `DeviceWebSocket`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- WebSocket callback performs parsing/queueing only.
- GPIO/actuator writes occur only through the existing safety-controlled actuator path.
- Queue length is bounded. Overflow rejects the new command with `failed/internal_error` rather than blocking network processing indefinitely.
- `set_mode adaptive` must return `rejected/phase_not_available` in Phase 4.
- `safe_stop` always requests monitor mode, LED PWM 0, and mixer OFF through the safety layer.
- Duplicate terminal `command_id` returns cached acknowledgement and does not repeat the physical action.
- Device token, Wi-Fi password, and operator secrets never enter command payloads.
- Device-side TTL begins at receipt uptime and uses monotonic time.

---

### Task 1: Add host-testable command DTO and parser

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/CommandModel.h`
- Create: `firmware/esp32/lib/BioVoltCore/CommandParser.h`
- Create: `firmware/esp32/lib/BioVoltCore/CommandParser.cpp`
- Create: `firmware/esp32/test/test_command_parser/test_main.cpp`

**Interfaces:**

```cpp
enum class CommandKind {
  SetMode,
  SetLedPwm,
  SetMixer,
  RequestStatus,
  SafeStop,
};

struct DeviceCommand {
  std::string commandId;
  std::string deviceId;
  std::string experimentId;
  uint32_t ttlMs{0};
  CommandKind kind;
  ControlMode requestedMode{ControlMode::Monitor};
  uint8_t requestedPwm{0};
  bool requestedMixerOn{false};
};

struct ParseCommandResult {
  bool valid{false};
  DeviceCommand command;
  std::string reasonCode;
};
```

- [ ] **Step 1: Write failing parser tests for all five command kinds**
- [ ] **Step 2: Add invalid schema version, missing ID, invalid PWM, and unknown kind tests**
- [ ] **Step 3: Implement parser with ArduinoJson and no hardware dependencies**
- [ ] **Step 4: Run native tests**

```bash
pio test -d firmware/esp32 -e native -f test_command_parser
```

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/lib/BioVoltCore/Command* firmware/esp32/test/test_command_parser
git commit -m "feat: parse BioVolt device commands on ESP32"
```

---

### Task 2: Add acknowledgement model and serializer

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/AckModel.h`
- Create: `firmware/esp32/lib/BioVoltCore/AckSerializer.h`
- Create: `firmware/esp32/lib/BioVoltCore/AckSerializer.cpp`
- Create: `firmware/esp32/test/test_ack_serializer/test_main.cpp`

**Interfaces:**

```cpp
enum class AckStatus { Accepted, Applied, Rejected, Failed };

struct DeviceAck {
  std::string commandId;
  std::string deviceId;
  AckStatus status;
  uint64_t uptimeMs{0};
  std::string reasonCode;
  std::string message;
  ActuatorState appliedState;
  bool includeAppliedState{false};
};
```

- [ ] **Step 1: Write exact-key applied acknowledgement test**
- [ ] **Step 2: Write rejected acknowledgement reason-code test**
- [ ] **Step 3: Implement serializer matching `device-ack.v1`**
- [ ] **Step 4: Verify no secrets or arbitrary diagnostic dump enters JSON**
- [ ] **Step 5: Run native tests and commit**

```bash
pio test -d firmware/esp32 -e native -f test_ack_serializer
git add firmware/esp32/lib/BioVoltCore/Ack* firmware/esp32/test/test_ack_serializer
git commit -m "feat: serialize BioVolt command acknowledgements"
```

---

### Task 3: Add command dedupe cache

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/CommandDedupe.h`
- Create: `firmware/esp32/test/test_command_dedupe/test_main.cpp`

**Interfaces:**

```cpp
class CommandDedupe {
 public:
  static constexpr size_t kCapacity = 32;
  bool find(const std::string& commandId, DeviceAck& ack) const;
  void remember(const std::string& commandId, const DeviceAck& terminalAck);
};
```

Use a fixed-capacity FIFO/ring buffer, not unbounded dynamic history.

- [ ] **Step 1: Write unseen/found tests**
- [ ] **Step 2: Write capacity eviction test**
- [ ] **Step 3: Implement fixed-capacity cache**
- [ ] **Step 4: Run and commit**

```bash
pio test -d firmware/esp32 -e native -f test_command_dedupe
git add firmware/esp32/lib/BioVoltCore/CommandDedupe.h firmware/esp32/test/test_command_dedupe
git commit -m "feat: deduplicate BioVolt ESP32 commands"
```

---

### Task 4: Add inbound WebSocket command queue

**Files:**
- Modify: `firmware/esp32/src/network/DeviceWebSocket.h`
- Modify: `firmware/esp32/src/network/DeviceWebSocket.cpp`
- Create: `firmware/esp32/src/runtime/CommandTask.h`
- Create: `firmware/esp32/src/runtime/CommandTask.cpp`
- Modify: `firmware/esp32/src/main.cpp`

Queue type:

```cpp
QueueHandle_t commandQueue = xQueueCreate(8, sizeof(CommandQueueItem));
```

Because `std::string` is not safe to memcpy through a FreeRTOS queue as a raw C++ object, define `CommandQueueItem` as a fixed-size POD structure with bounded char arrays and scalar fields.

- [ ] **Step 1: Define fixed-size queue DTO with command ID/device ID/experiment ID buffers**
- [ ] **Step 2: In WebSocket text callback, parse then enqueue with zero wait**
- [ ] **Step 3: On full queue, immediately send failed acknowledgement when command ID can be recovered**
- [ ] **Step 4: Create `CommandTask` at priority 3 with stack sized after measurement, initial target 4096**
- [ ] **Step 5: Build ESP32 target**

```bash
pio run -d firmware/esp32 -e esp32dev
```

- [ ] **Step 6: Commit**

```bash
git add firmware/esp32/src/network firmware/esp32/src/runtime/CommandTask.* firmware/esp32/src/main.cpp
git commit -m "feat: queue BioVolt device commands outside websocket callback"
```

---

### Task 5: Implement Passive/Manual execution policy

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/CommandPolicy.h`
- Create: `firmware/esp32/test/test_command_policy/test_main.cpp`
- Modify: `firmware/esp32/src/runtime/CommandTask.cpp`

Policy rules:

```text
set_mode monitor  -> allowed
set_mode passive  -> allowed
set_mode manual   -> allowed
set_mode adaptive -> reject phase_not_available

set_led_pwm -> allowed only passive/manual
set_mixer   -> allowed only manual in Phase 4
safe_stop   -> always allowed
request_status -> always allowed
```

Safety rules are applied after policy rules. For example a manual mixer-on request can still be rejected by cooldown.

- [ ] **Step 1: Write host tests for mode/command matrix**
- [ ] **Step 2: Implement pure policy function**
- [ ] **Step 3: In CommandTask, check dedupe then TTL then policy**
- [ ] **Step 4: Route actuator requests through `ActuatorController`/queue and read back actual applied state**
- [ ] **Step 5: Return `applied` only after state store reflects actual applied outputs**
- [ ] **Step 6: Cache terminal ack in dedupe cache**
- [ ] **Step 7: Run tests/build and commit**

```bash
pio test -d firmware/esp32 -e native -f test_command_policy
pio run -d firmware/esp32 -e esp32dev
git add firmware/esp32/lib/BioVoltCore/CommandPolicy.h firmware/esp32/test/test_command_policy firmware/esp32/src/runtime/CommandTask.cpp
git commit -m "feat: execute safe Passive and Manual commands on ESP32"
```

---

### Task 6: Send acknowledgements over existing WebSocket

**Files:**
- Modify: `firmware/esp32/src/network/DeviceWebSocket.h`
- Modify: `firmware/esp32/src/network/DeviceWebSocket.cpp`
- Modify: `firmware/esp32/src/runtime/CommandTask.cpp`

**Interface:**

```cpp
bool sendAck(const DeviceAck& ack);
```

`sendAck` serializes `device-ack.v1` and calls the same WebSocket client's text send primitive used by telemetry.

- [ ] **Step 1: Add connected send-ack path**
- [ ] **Step 2: If disconnected after command application, retain only the latest terminal ack for each in-flight command in the bounded dedupe cache**
- [ ] **Step 3: On reconnect, do not proactively replay all cached acks; duplicate command delivery causes the cached terminal ack to be returned**
- [ ] **Step 4: Upload and manually verify command -> ack lifecycle against backend**
- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/src/network/DeviceWebSocket.* firmware/esp32/src/runtime/CommandTask.cpp
git commit -m "feat: acknowledge applied BioVolt ESP32 commands"
```

## Module 4.4 Exit Criteria

- [ ] WebSocket callback never directly changes hardware.
- [ ] Command queue is bounded and uses POD-safe storage.
- [ ] Duplicate command ID does not repeat actuator effect.
- [ ] Expired TTL rejects before application.
- [ ] Adaptive mode is rejected in Phase 4.
- [ ] Manual mixer command cannot bypass firmware cooldown/runtime safety.
- [ ] `applied_state` reports actual post-safety outputs.
- [ ] Acknowledgements conform to the shared schema.
