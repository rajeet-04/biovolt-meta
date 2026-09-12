# Phase 3.2: Runtime Configuration, NVS, Secrets, and Serial Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure the real ESP32 for laptop hotspot, backend target, device identity, and actuator safety limits without hard-coding operational values into drivers, while keeping secrets redacted and configuration changes deterministic.

**Architecture:** Compile-time board wiring lives in `BoardConfig.h`. Host-testable runtime configuration lives in `lib/BioVoltCore/RuntimeConfig.h`. At startup, firmware loads one versioned JSON configuration blob from Preferences/NVS, falling back to an ignored local `BuildSecrets.h` only when no valid NVS config exists. The active configuration is immutable for the current boot. Serial provisioning edits a draft, validates it, stores the complete blob, and requires reboot to apply network/device changes.

**Tech Stack:** C++17, ESP32 Preferences, ArduinoJson 6.x, Arduino Serial, PlatformIO native tests.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- `BuildSecrets.h` is ignored by Git and never committed.
- Passwords and tokens never appear in clear-text logs or `config show` output.
- Preferences namespace is `biovolt`.
- The persisted key is one complete versioned blob: `config_v1`.
- Device ID and cell ID are non-empty and maximum 64 characters.
- Backend path defaults to `/ws/device`; backend port defaults to `8000`.
- No specific laptop hotspot IP is assumed in committed files.
- PWM safety bounds stay within `0..255`; mixer max runtime is positive and cooldown non-negative.
- Active config is loaded once during boot and is not mutated while Sensor/Telemetry tasks are running.
- `config save` writes the validated draft for the next reboot.
- Sensor drivers consume `BoardConfig`, not runtime network config.

---

### Task 1: Define board wiring constants

**Files:**
- Create: `firmware/esp32/include/BoardConfig.h`
- Modify: `firmware/esp32/README.md`

**Interfaces:**

```cpp
namespace BoardConfig {
constexpr int kI2cSda = 21;
constexpr int kI2cScl = 22;
constexpr int kDs18b20Pin = 19;
constexpr int kProbeLed680Pin = 25;
constexpr int kGrowLedPwmPin = 26;
constexpr int kMixerPin = 27;
constexpr uint8_t kAds1115Address = 0x48;
constexpr uint8_t kBh1750Address = 0x23;
constexpr uint8_t kBpvChannel = 0;
constexpr uint8_t kOpticalChannel = 1;
}
```

- [ ] **Step 1: Create constants in one header**

No sensor/actuator driver may duplicate numeric pin values.

- [ ] **Step 2: Document driver-stage warning**

GPIO 25/26/27 are logic outputs only. Probe LED, grow-light load, and mixer require suitable external driver stages.

- [ ] **Step 3: Build target**

```bash
cd firmware/esp32
pio run -e esp32dev
```

- [ ] **Step 4: Commit**

```bash
git add include/BoardConfig.h README.md
git commit -m "feat: define BioVolt ESP32 board mapping"
```

---

### Task 2: Define host-testable runtime configuration and validation

**Files:**
- Create: `firmware/esp32/lib/BioVoltCore/RuntimeConfig.h`
- Create: `firmware/esp32/lib/BioVoltCore/ConfigValidation.h`
- Create: `firmware/esp32/test/test_config_validation/test_main.cpp`

**Interfaces:**

```cpp
struct RuntimeConfig {
  std::string wifiSsid;
  std::string wifiPassword;
  std::string backendHost;
  uint16_t backendPort{8000};
  std::string backendPath{"/ws/device"};
  std::string deviceId;
  std::string cellId;
  std::string deviceToken;
  uint8_t ledPwmMin{0};
  uint8_t ledPwmMax{255};
  uint16_t mixerMaxRuntimeS{10};
  uint16_t mixerCooldownS{60};
};

struct ConfigValidationResult {
  bool valid;
  const char* message;
};

ConfigValidationResult validateRuntimeConfig(const RuntimeConfig& config);
```

- [ ] **Step 1: Write failing validation tests**

Cover:

```text
blank SSID
blank backendHost
blank deviceId/cellId/token
backendPort == 0
backendPath not beginning with '/'
ID length >64
ledPwmMin > ledPwmMax
mixerMaxRuntimeS == 0
valid normal configuration
```

- [ ] **Step 2: Implement validation without Arduino dependencies**

This file must compile in `env:native`.

- [ ] **Step 3: Run native tests**

```bash
pio test -e native -f test_config_validation
```

- [ ] **Step 4: Commit**

```bash
git add lib/BioVoltCore/RuntimeConfig.h lib/BioVoltCore/ConfigValidation.h test/test_config_validation
git commit -m "feat: validate BioVolt device runtime configuration"
```

---

### Task 3: Add ignored first-boot secret fallback

**Files:**
- Create: `firmware/esp32/include/BuildSecrets.example.h`
- Modify: root `.gitignore`
- Modify: `firmware/esp32/README.md`

**Interfaces:**

Committed example contains placeholders only:

```cpp
#pragma once
#define BIOVOLT_WIFI_SSID ""
#define BIOVOLT_WIFI_PASSWORD ""
#define BIOVOLT_BACKEND_HOST ""
#define BIOVOLT_DEVICE_ID "biovolt-01"
#define BIOVOLT_CELL_ID "cell-a"
#define BIOVOLT_DEVICE_TOKEN ""
```

- [ ] **Step 1: Ignore local file**

Add:

```text
firmware/esp32/include/BuildSecrets.h
```

to root `.gitignore`.

- [ ] **Step 2: Document first-boot copy**

```bash
cp firmware/esp32/include/BuildSecrets.example.h firmware/esp32/include/BuildSecrets.h
```

The backend host is discovered from the actual laptop hotspot/network and is never assumed by the committed example.

- [ ] **Step 3: Verify ignore rule**

```bash
git check-ignore firmware/esp32/include/BuildSecrets.h
```

Expected: ignored path is printed.

- [ ] **Step 4: Commit only safe files**

```bash
git add firmware/esp32/include/BuildSecrets.example.h .gitignore firmware/esp32/README.md
git commit -m "chore: add local BioVolt firmware secret fallback"
```

---

### Task 4: Persist one versioned config blob in Preferences/NVS

**Files:**
- Create: `firmware/esp32/src/config/ConfigStore.h`
- Create: `firmware/esp32/src/config/ConfigStore.cpp`

**Interfaces:**

```cpp
class ConfigStore {
 public:
  bool begin();
  RuntimeConfig load(const RuntimeConfig& fallback);
  bool save(const RuntimeConfig& config);
  void clear();
};
```

Persist one JSON object under key `config_v1`:

```json
{
  "version": 1,
  "wifi_ssid": "...",
  "wifi_password": "...",
  "backend_host": "...",
  "backend_port": 8000,
  "backend_path": "/ws/device",
  "device_id": "biovolt-01",
  "cell_id": "cell-a",
  "device_token": "...",
  "led_pwm_min": 0,
  "led_pwm_max": 255,
  "mixer_max_runtime_s": 10,
  "mixer_cooldown_s": 60
}
```

- [ ] **Step 1: Validate before serialization**

If draft config is invalid, return false before touching Preferences.

- [ ] **Step 2: Serialize complete blob in memory**

Use a bounded ArduinoJson document and ensure serialization succeeds before the single `putString("config_v1", blob)` write.

- [ ] **Step 3: Load defensively**

On absent blob, parse failure, wrong version, or validation failure:

```text
log safe reason
use fallback RuntimeConfig
```

Do not print the blob because it contains secrets.

- [ ] **Step 4: Clear only project key/namespace**

`clear()` removes the BioVolt stored configuration, not unrelated device preferences.

- [ ] **Step 5: Build and commit**

```bash
pio run -e esp32dev
git add src/config
git commit -m "feat: persist versioned BioVolt configuration blob in NVS"
```

---

### Task 5: Implement serial provisioner over a draft config

**Files:**
- Create: `firmware/esp32/src/provisioning/SerialProvisioner.h`
- Create: `firmware/esp32/src/provisioning/SerialProvisioner.cpp`
- Modify: `firmware/esp32/README.md`

**Interfaces:**

```cpp
class SerialProvisioner {
 public:
  void begin(const RuntimeConfig& activeConfig, ConfigStore& store);
  void poll();
};
```

Supported commands:

```text
config show
config set ssid <value>
config set wifi_password <value>
config set backend_host <value>
config set backend_port <value>
config set device_id <value>
config set cell_id <value>
config set token <value>
config set pwm_min <0-255>
config set pwm_max <0-255>
config set mixer_max_runtime_s <value>
config set mixer_cooldown_s <value>
config save
config discard
config reset
status
reboot
```

- [ ] **Step 1: Copy active config into internal draft**

`config set` mutates only the draft. It never changes the `RuntimeConfig` already passed to NetworkManager/TelemetryTask.

- [ ] **Step 2: Implement bounded line parser**

Reject lines longer than 256 bytes and malformed/out-of-range integers.

- [ ] **Step 3: Redact secret output**

`config show` may print:

```text
ssid=BioVolt-Hotspot
wifi_password=<configured>
backend_host=192.168.x.x
backend_port=8000
device_id=biovolt-01
cell_id=cell-a
token=<configured>
pwm_min=0
pwm_max=255
mixer_max_runtime_s=10
mixer_cooldown_s=60
```

- [ ] **Step 4: Define save/apply semantics**

`config save`:

```text
validate draft
persist complete config_v1 blob
print "saved; reboot required to apply"
```

It must not restart Wi-Fi or mutate the active runtime in-place.

- [ ] **Step 5: Add safe `status` diagnostic**

Print only non-secret operational fields:

```text
uptime_ms=<esp_timer_get_time()/1000>
free_heap_bytes=<ESP.getFreeHeap()>
device_id=<active device id>
cell_id=<active cell id>
backend_host=<active host>
backend_port=<active port>
config_pending=<true|false>
```

Never print password/token.

- [ ] **Step 6: Build and bench-test parser**

```bash
pio run -e esp32dev -t upload
pio device monitor -b 115200
```

- [ ] **Step 7: Commit**

```bash
git add src/provisioning README.md
git commit -m "feat: provision BioVolt ESP32 configuration over serial"
```

---

### Task 6: Define startup configuration flow

**Files:**
- Modify: `firmware/esp32/src/main.cpp`

**Interfaces:**

Startup order:

```text
initialize Serial
force actuator pins safe
ConfigStore.begin()
build local BuildSecrets fallback
ConfigStore.load(fallback)
validate active config
initialize SerialProvisioner with active config + store
initialize remaining runtime components with const active config
start FreeRTOS tasks in Module 3.5
```

- [ ] **Step 1: Keep active config lifetime stable**

Store one application-owned `RuntimeConfig` object for the entire boot. Consumers receive `const RuntimeConfig&` or pointers treated as immutable.

- [ ] **Step 2: Define invalid-total-config degraded mode**

If both NVS and fallback are invalid:

```text
actuators stay OFF
sensor bench operation may initialize
network/telemetry do not start
serial provisioning remains available
```

This allows repair without reflashing.

- [ ] **Step 3: Build target**

```bash
pio run -e esp32dev
```

- [ ] **Step 4: Commit**

```bash
git add src/main.cpp
git commit -m "feat: load immutable BioVolt runtime configuration at boot"
```

## Module 3.2 Exit Criteria

- [ ] Board wiring has one source of truth.
- [ ] RuntimeConfig/validation compile in native tests.
- [ ] No committed file assumes a laptop hotspot IP.
- [ ] NVS stores one validated `config_v1` blob.
- [ ] Invalid/corrupt stored config falls back safely.
- [ ] Local secret file is ignored.
- [ ] Serial CLI edits a draft and requires reboot to apply saved changes.
- [ ] `status` exposes uptime/free heap without secrets.
- [ ] Active runtime configuration remains immutable during a boot session.
