# Phase 3.6: Device Telemetry Serialization, Wi-Fi, and WebSocket Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stream exact real-device `device-telemetry.v1` frames to the unchanged FastAPI `/ws/device` endpoint at normal 500 ms cadence with authenticated headers, reconnect behavior, and no simulator-specific logic.

**Architecture:** Native-testable `TelemetryModel` and `TelemetrySerializer` live in `lib/BioVoltCore`. ESP32-only `NetworkManager`, `DeviceWebSocket`, and `TelemetryTask` live under `src/`. TelemetryTask snapshots runtime state, advances sequence on every scheduled tick, serializes one live frame, and either sends it immediately or discards it if disconnected. There is no flash queue or stale replay.

**Tech Stack:** WiFi.h, Links2004 WebSocketsClient, ArduinoJson 6.x, FreeRTOS, `esp_timer_get_time()`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Use the same `/ws/device` endpoint as the simulator.
- Headers are exactly `X-BioVolt-Device-ID` plus `Authorization: Bearer <token>`.
- Token/Wi-Fi password are never logged.
- Raw JSON contains no current, power, OD680, biomass, carbon, cumulative energy, or server timestamp.
- `uptime_ms` comes from `esp_timer_get_time()/1000ULL`.
- `sequence` advances once per scheduled telemetry tick, even while disconnected.
- No offline replay/backfill is attempted in Phase 3.
- Reconnect uses bounded 1, 2, 4, 8, 10 second backoff.
- Wi-Fi/WebSocket work must not block SensorTask or ActuatorTask.
- Active `RuntimeConfig` is read-only for the boot session.
- Anything run in `env:native` lives in `lib/BioVoltCore`, not ESP32-only `src/`.

---

### Task 1: Implement host-testable telemetry model and serializer

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/TelemetryModel.h`
- Create: `firmware/esp32/lib/BioVoltCore/TelemetrySerializer.h`
- Create: `firmware/esp32/lib/BioVoltCore/TelemetrySerializer.cpp`
- Create: `firmware/esp32/test/test_telemetry_model/test_main.cpp`

**Interfaces:**

```cpp
struct TelemetryEnvelope {
  const char* deviceId;
  const char* cellId;
  uint32_t sequence;
  uint64_t uptimeMs;
  RuntimeSnapshot runtime;
};

class TelemetrySerializer {
 public:
  static constexpr size_t kJsonCapacity = 1536;
  bool serialize(const TelemetryEnvelope& envelope,
                 char* output,
                 size_t outputSize,
                 size_t& written) const;
};
```

- [ ] **Step 1: Write failing native test for exact top-level keys**

Assert:

```text
schema_version
device_id
sequence
uptime_ms
cell_id
electrical
optical
environment
actuators
control
health
```

- [ ] **Step 2: Assert exact nested field names**

```text
electrical: bpv_voltage_mv, bpv_adc_raw
optical: bpw34_raw, bpw34_voltage_mv, led_680_enabled
environment: temperature_c, lux
actuators: grow_led_pwm, mixer_on
control: mode, optimizer_direction
health: ads1115_ok, bpw34_ok, temperature_ok, light_sensor_ok
```

- [ ] **Step 3: Write forbidden-derived-field test**

Serialized JSON must not contain:

```text
current_ua
power_uw
od680
biomass
co2_biofixed
cumulative_energy
timestamp
```

- [ ] **Step 4: Write null/health test**

Invalid temperature produces JSON `null` with `temperature_ok=false`. Repeat at least one ADC-null test.

- [ ] **Step 5: Implement serializer using ArduinoJson**

Use `StaticJsonDocument<kJsonCapacity>` and explicit nested objects. `ControlMode` maps exactly:

```text
Monitor -> monitor
Passive -> passive
Adaptive -> adaptive
Manual -> manual
```

Even though Phase 3 runtime stays Monitor, serializer supports the existing contract enum for later compatibility.

- [ ] **Step 6: Assert normal fully populated frame fits capacity**

The test must verify serialization returns success, `written > 0`, and `written < outputSize`.

- [ ] **Step 7: Run native tests and commit**

```bash
cd firmware/esp32
pio test -e native -f test_telemetry_model
git add lib/BioVoltCore/TelemetryModel.h lib/BioVoltCore/TelemetrySerializer.* test/test_telemetry_model
git commit -m "feat: serialize real ESP32 telemetry contract"
```

---

### Task 2: Implement non-blocking Wi-Fi state manager

**Files:**
- Create: `firmware/esp32/src/network/NetworkManager.h`
- Create: `firmware/esp32/src/network/NetworkManager.cpp`

**Interfaces:**

```cpp
enum class NetworkState { Disconnected, Connecting, Connected };

class NetworkManager {
 public:
  void begin(const RuntimeConfig& config);
  void poll(uint64_t nowMs);
  bool connected() const;
  NetworkState state() const;
};
```

- [ ] **Step 1: Use active config by const reference/copy**

Do not observe the provisioning draft.

- [ ] **Step 2: Disable unnecessary Wi-Fi credential persistence**

NVS `config_v1` is the BioVolt source of truth.

- [ ] **Step 3: Start connection without blocking loop**

Never use:

```cpp
while (WiFi.status() != WL_CONNECTED) { ... }
```

`poll()` observes status and schedules retries.

- [ ] **Step 4: Apply bounded retry timing**

Use `reconnectDelayMs(attempt)` after failed/disconnected attempts and reset the attempt count on a stable successful connection.

- [ ] **Step 5: Log safe state only**

Allowed examples:

```text
Wi-Fi connecting
Wi-Fi connected, IP=...
Wi-Fi disconnected
```

Never print password.

- [ ] **Step 6: Build and commit**

```bash
pio run -e esp32dev
git add src/network/NetworkManager.*
git commit -m "feat: reconnect BioVolt ESP32 Wi-Fi without blocking hardware tasks"
```

---

### Task 3: Implement authenticated WebSocket device client

**Files:**
- Create: `firmware/esp32/src/network/DeviceWebSocket.h`
- Create: `firmware/esp32/src/network/DeviceWebSocket.cpp`

**Interfaces:**

```cpp
enum class WebSocketState { Disconnected, Connecting, Connected };

class DeviceWebSocket {
 public:
  void begin(const RuntimeConfig& config);
  void poll(uint64_t nowMs, bool networkConnected);
  bool connected() const;
  bool sendText(const char* payload, size_t length);
  WebSocketState state() const;
};
```

- [ ] **Step 1: Build exact extra headers without logging token**

```text
X-BioVolt-Device-ID: <device-id>\r\n
Authorization: Bearer <token>\r\n
```

- [ ] **Step 2: Connect to configured host/port/path**

Normal local shape:

```text
ws://<actual-laptop-hotspot-ip>:8000/ws/device
```

No Nginx dependency in Phase 3.

- [ ] **Step 3: Define network-down behavior explicitly**

When `networkConnected == false`:

```text
close/reset WebSocket if necessary
state = Disconnected
do not attempt socket reconnect until Wi-Fi returns
```

This prevents stale socket state surviving a Wi-Fi outage.

- [ ] **Step 4: Service WebSocketsClient frequently when network exists**

Call `webSocket.loop()` around every 20 ms from TelemetryTask.

- [ ] **Step 5: Ignore control execution in Phase 3**

Incoming server text may be logged only as a compact safe protocol diagnostic. It must never directly set PWM, mixer, or mode.

- [ ] **Step 6: Reset reconnect attempts after successful socket connection**

Apply bounded backoff after later disconnects.

- [ ] **Step 7: Build and commit**

```bash
pio run -e esp32dev
git add src/network/DeviceWebSocket.*
git commit -m "feat: authenticate real ESP32 to BioVolt device websocket"
```

---

### Task 4: Implement TelemetryTask

**Files:**
- Create: `firmware/esp32/src/telemetry/TelemetryTask.h`
- Create: `firmware/esp32/src/telemetry/TelemetryTask.cpp`
- Modify: `firmware/esp32/src/main.cpp`

**Interfaces:**

```cpp
struct TelemetryTaskContext {
  RuntimeStateStore* state;
  NetworkManager* network;
  DeviceWebSocket* websocket;
  const RuntimeConfig* config;
};

void telemetryTaskEntry(void* context);
```

- [ ] **Step 1: Maintain a scheduled 500 ms telemetry clock independent of connectivity**

At each scheduled tick:

```text
copy RuntimeSnapshot
sequence++
set uptime from esp_timer_get_time()/1000
serialize envelope
if WebSocket connected -> send now
else -> discard serialized frame
```

- [ ] **Step 2: Do not queue stale JSON**

No in-RAM backlog and no flash backlog are introduced. Reconnect sends current reactor state only.

- [ ] **Step 3: Service connection every 20 ms**

```cpp
network.poll(nowMs);
websocket.poll(nowMs, network.connected());
vTaskDelay(pdMS_TO_TICKS(20));
```

Use monotonic time comparisons so scheduler recovery does not emit an uncontrolled burst after a long stall. If more than one telemetry period was missed inside the task, advance the schedule to the next future slot and account for missed sequence ticks deterministically rather than replaying frames.

- [ ] **Step 4: Start TelemetryTask independently**

Recommended priority `2`, stack `6144`. Take a runtime snapshot under mutex, then serialize/send after the lock is released.

- [ ] **Step 5: Verify serial lifecycle logs**

Expected compact transitions:

```text
Wi-Fi connected
WebSocket connected
WebSocket disconnected
Wi-Fi disconnected
```

Do not print each payload in normal build.

- [ ] **Step 6: Commit**

```bash
git add src/telemetry src/network src/main.cpp
git commit -m "feat: stream real ESP32 telemetry to BioVolt backend"
```

---

### Task 5: Verify backend contract compatibility with simulator stopped

**Files:**
- Modify: `firmware/esp32/README.md`

- [ ] **Step 1: Stop simulator and start backend**

```bash
docker compose stop simulator || true
docker compose up -d backend
```

- [ ] **Step 2: Discover actual laptop hotspot IP**

Document OS-specific discovery generically; do not assume a committed IP address.

- [ ] **Step 3: Provision ESP32 and reboot**

Set SSID/password, actual backend host, port 8000, device ID, cell ID, and shared token. `config save` then `reboot`.

- [ ] **Step 4: Confirm system status**

```bash
curl http://localhost:8000/api/system/status
```

Expected configured real device ID is connected.

- [ ] **Step 5: Confirm processed telemetry**

```bash
curl "http://localhost:8000/api/telemetry/latest?device_id=biovolt-01&cell_id=cell-a"
```

When raw BPV voltage is valid and backend load resistance is configured, processed current/power are backend-derived. OD680 remains null until valid backend optical references exist.

- [ ] **Step 6: Commit compatibility instructions**

```bash
git add README.md
git commit -m "docs: document real ESP32 backend connection workflow"
```

## Module 3.6 Exit Criteria

- [ ] Telemetry serializer compiles and is tested under native environment.
- [ ] Serializer matches exact Phase 0 raw contract and forbids backend-derived fields.
- [ ] Invalid sensors become JSON null plus false health flags.
- [ ] Device token is only transmitted as auth material and never logged.
- [ ] Wi-Fi and WebSocket reconnect without blocking hardware tasks.
- [ ] Socket state is explicitly reset when Wi-Fi disappears.
- [ ] Telemetry normally transmits every 500 ms.
- [ ] Sequence advances through unsent periods; stale frames are never replayed.
- [ ] Real device reaches unchanged `/ws/device` with simulator stopped.
