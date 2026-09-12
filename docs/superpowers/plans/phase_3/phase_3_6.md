# Phase 3.6: Device Telemetry Serialization, Wi-Fi, and WebSocket Transport Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stream exact real-device `device-telemetry.v1` frames to the unchanged FastAPI `/ws/device` endpoint at normal 500 ms cadence with authenticated headers, reconnect behavior, and no simulator-specific logic.

**Architecture:** `TelemetrySerializer` converts a coherent `RuntimeSnapshot` into the Phase 0 raw JSON contract. `NetworkManager` owns Wi-Fi state. `DeviceWebSocket` owns authenticated WebSocket lifecycle. `TelemetryTask` services connection state frequently while producing one scheduled frame every 500 ms. No flash queue or stale-frame replay is introduced.

**Tech Stack:** WiFi.h, Links2004 WebSocketsClient, ArduinoJson 6.x, FreeRTOS, `esp_timer_get_time()`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Use `/ws/device`, not a hardware-only endpoint.
- Headers are `X-BioVolt-Device-ID` and `Authorization: Bearer <token>`.
- Never log token or Wi-Fi password.
- Raw JSON contains no current, power, OD680, biomass, carbon, cumulative energy, or wall-clock timestamp.
- `uptime_ms` comes from `esp_timer_get_time()/1000` as monotonic 64-bit milliseconds.
- `sequence` advances once per scheduled telemetry frame, including periods when the frame cannot be delivered because the network is down.
- No offline replay is attempted in Phase 3.
- Reconnect uses bounded 1, 2, 4, 8, 10 second backoff.
- Telemetry/network work must not block SensorTask or ActuatorTask.

---

### Task 1: Define telemetry model and serializer tests

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/TelemetryModel.h`
- Create: `firmware/esp32/src/telemetry/TelemetrySerializer.h`
- Create: `firmware/esp32/src/telemetry/TelemetrySerializer.cpp`
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

- [ ] **Step 1: Write native test for exact required top-level keys**

Parse serialized JSON and assert:

```text
schema_version, device_id, sequence, uptime_ms, cell_id,
electrical, optical, environment, actuators, control, health
```

- [ ] **Step 2: Write forbidden-field test**

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

- [ ] **Step 3: Write null/health test**

An invalid DS18B20 value must serialize as:

```json
"temperature_c": null
```

with:

```json
"temperature_ok": false
```

- [ ] **Step 4: Implement serializer using ArduinoJson**

Use `StaticJsonDocument<kJsonCapacity>` and explicit nested objects. Convert `ControlMode` to exact strings:

```text
Monitor -> monitor
Passive -> passive
Adaptive -> adaptive
Manual -> manual
```

- [ ] **Step 5: Assert canonical real frame fits capacity**

Test `written < kJsonCapacity` with all fields populated.

- [ ] **Step 6: Run native tests and commit**

```bash
pio test -e native -f test_telemetry_model
git add firmware/esp32/lib/BioVoltCore/TelemetryModel.h firmware/esp32/src/telemetry firmware/esp32/test/test_telemetry_model
git commit -m "feat: serialize real ESP32 telemetry contract"
```

---

### Task 2: Implement Wi-Fi state manager

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

- [ ] **Step 1: Disable Wi-Fi persistence of plaintext config when not needed**

Runtime/NVS config remains the project source of truth.

- [ ] **Step 2: Implement non-blocking connection attempts**

Do not sit in `while (WiFi.status() != WL_CONNECTED)` loops. Start connection and poll status from TelemetryTask.

- [ ] **Step 3: Use bounded retry timing**

After disconnect, schedule reconnect using `reconnectDelayMs(attempt)`.

- [ ] **Step 4: Log safe state only**

Allowed:

```text
Wi-Fi connecting to configured SSID
Wi-Fi connected, IP=...
Wi-Fi disconnected
```

Never print password.

- [ ] **Step 5: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/network/NetworkManager.*
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

- [ ] **Step 1: Build exact extra headers**

Expected:

```text
X-BioVolt-Device-ID: biovolt-01\r\n
Authorization: Bearer <token>\r\n
```

Use the WebSocketsClient extra-header API before connect.

- [ ] **Step 2: Connect to configured host/port/path**

Normal local target:

```text
ws://<laptop-hotspot-ip>:8000/ws/device
```

No Nginx dependency in Phase 3.

- [ ] **Step 3: Service `webSocket.loop()` frequently**

Call from TelemetryTask at roughly 10-20 ms intervals while connected/connecting.

- [ ] **Step 4: Handle server text defensively**

Phase 3 does not execute control commands. Incoming text is limited to safe diagnostics and future-protocol logging. Do not treat arbitrary incoming JSON as actuator instructions.

- [ ] **Step 5: Reset reconnect attempt after successful connection**

Use bounded backoff again after later disconnects.

- [ ] **Step 6: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/network/DeviceWebSocket.*
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
  RuntimeConfig* config;
};

void telemetryTaskEntry(void* context);
```

- [ ] **Step 1: Use a 500 ms telemetry scheduler independent of connection state**

Maintain `nextTelemetryAtMs`. At every scheduled tick:

```text
snapshot runtime state
sequence++
construct envelope with monotonic uptime
serialize
if websocket connected -> send
else -> discard frame after sequence advancement
```

- [ ] **Step 2: Do not queue unsent JSON**

This guarantees reconnect resumes live state instead of replaying stale reactor conditions.

- [ ] **Step 3: Service network/WebSocket every 20 ms**

Between telemetry ticks:

```cpp
network.poll(nowMs);
websocket.poll(nowMs, network.connected());
vTaskDelay(pdMS_TO_TICKS(20));
```

- [ ] **Step 4: Start TelemetryTask separately from hardware tasks**

Recommended priority 2, stack 6144. Do not hold the runtime mutex during serialization/network send after taking the snapshot copy.

- [ ] **Step 5: Upload and verify serial connection lifecycle**

Expected sequence:

```text
Wi-Fi connected
WebSocket connected
telemetry send sequence=...
```

Do not log every payload in normal build.

- [ ] **Step 6: Commit**

```bash
git add firmware/esp32/src/telemetry firmware/esp32/src/network firmware/esp32/src/main.cpp
git commit -m "feat: stream real ESP32 telemetry to BioVolt backend"
```

---

### Task 5: Verify contract compatibility against backend without simulator

**Files:**
- Modify: `firmware/esp32/README.md`

- [ ] **Step 1: Stop simulator**

```bash
docker compose stop simulator
```

- [ ] **Step 2: Run backend**

```bash
docker compose up -d backend
```

- [ ] **Step 3: Configure ESP32 backend host/token and reboot**

Use serial provisioning from Module 3.2.

- [ ] **Step 4: Confirm backend sees device**

```bash
curl http://localhost:8000/api/system/status
```

Expected connected device includes configured real device ID.

- [ ] **Step 5: Confirm latest telemetry**

```bash
curl "http://localhost:8000/api/telemetry/latest?device_id=biovolt-01&cell_id=cell-a"
```

Expected backend-processed data contains current/power based on real BPV voltage when calibration/config permits.

- [ ] **Step 6: Commit compatibility instructions**

```bash
git add firmware/esp32/README.md
git commit -m "docs: document real ESP32 backend connection workflow"
```

## Module 3.6 Exit Criteria

- [ ] Serializer matches the raw Phase 0 contract.
- [ ] Invalid sensors become JSON null plus false health flags.
- [ ] Device token is sent only as auth header and never logged.
- [ ] Wi-Fi and WebSocket reconnection are non-blocking.
- [ ] Telemetry normally transmits every 500 ms.
- [ ] Sequence advances through connection outages.
- [ ] Unsent frames are not replayed.
- [ ] Real device reaches unchanged `/ws/device` with simulator stopped.
