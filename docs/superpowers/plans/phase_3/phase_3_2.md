# Phase 3.2: Runtime Configuration, NVS, Secrets, and Serial Provisioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the real ESP32 configurable for laptop hotspot, backend target, device identity, and safety limits without hard-coding operational values into sensor/network drivers.

**Architecture:** Compile-time board wiring lives in `BoardConfig.h`. Runtime connection/device settings live in a typed `RuntimeConfig`, persist in ESP32 Preferences/NVS, and may fall back to a local ignored `BuildSecrets.h` on first boot. A serial provisioning CLI provides hackathon-friendly reconfiguration without reflashing while redacting credentials.

**Tech Stack:** C++17, ESP32 Preferences, Arduino Serial, PlatformIO native tests for pure validation.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- `BuildSecrets.h` is ignored by Git and never committed.
- Passwords and tokens must never be printed in clear text.
- NVS namespace is `biovolt`.
- Device ID and cell ID are non-empty and maximum 64 characters.
- Backend path defaults to `/ws/device`.
- Backend port defaults to `8000`.
- PWM safety bounds must remain inside 0..255.
- Mixer max runtime is positive; cooldown is non-negative.
- Sensor drivers consume board constants, not runtime network configuration.

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

No driver may duplicate numeric pin values.

- [ ] **Step 2: Document driver-stage warning**

State that GPIO 25/26/27 are logic outputs and must not directly power the LED/mixer loads.

- [ ] **Step 3: Build ESP32 target**

```bash
pio run -e esp32dev
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/include/BoardConfig.h firmware/esp32/README.md
git commit -m "feat: define BioVolt ESP32 board mapping"
```

---

### Task 2: Define runtime configuration model and validation

**Files:**
- Create: `firmware/esp32/src/config/RuntimeConfig.h`
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

ConfigValidationResult validateRuntimeConfig(const RuntimeConfig& config);
```

- [ ] **Step 1: Write failing validation tests**

Cover blank SSID, blank backend host, blank device/cell/token, `ledPwmMin > ledPwmMax`, zero mixer max runtime, and valid default port/path.

- [ ] **Step 2: Implement validator without Arduino dependencies**

Return a structured result with `valid` and a short field-specific message.

- [ ] **Step 3: Run native tests**

```bash
pio test -e native -f test_config_validation
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/src/config/RuntimeConfig.h firmware/esp32/lib/BioVoltCore/ConfigValidation.h firmware/esp32/test/test_config_validation
git commit -m "feat: validate BioVolt device runtime configuration"
```

---

### Task 3: Add ignored build-secret fallback

**Files:**
- Create: `firmware/esp32/include/BuildSecrets.example.h`
- Modify: `.gitignore`
- Modify: `firmware/esp32/README.md`

**Interfaces:**

Example file defines placeholders only:

```cpp
#pragma once
#define BIOVOLT_WIFI_SSID ""
#define BIOVOLT_WIFI_PASSWORD ""
#define BIOVOLT_BACKEND_HOST "192.168.137.1"
#define BIOVOLT_DEVICE_ID "biovolt-01"
#define BIOVOLT_CELL_ID "cell-a"
#define BIOVOLT_DEVICE_TOKEN ""
```

- [ ] **Step 1: Ignore local secret file**

Add `firmware/esp32/include/BuildSecrets.h` to root `.gitignore`.

- [ ] **Step 2: Document first-boot workflow**

```bash
cp firmware/esp32/include/BuildSecrets.example.h firmware/esp32/include/BuildSecrets.h
```

Then edit local values only.

- [ ] **Step 3: Verify Git ignores the local secret path**

```bash
git check-ignore firmware/esp32/include/BuildSecrets.h
```

Expected: path is ignored.

- [ ] **Step 4: Commit only example/docs/ignore rules**

```bash
git add firmware/esp32/include/BuildSecrets.example.h .gitignore firmware/esp32/README.md
git commit -m "chore: add local BioVolt firmware secret fallback"
```

---

### Task 4: Persist runtime configuration in Preferences/NVS

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

Use short stable NVS keys under namespace `biovolt`, including:

```text
ssid, wifi_pw, host, port, path, device_id, cell_id, token,
pwm_min, pwm_max, mix_max, mix_cool
```

- [ ] **Step 1: Implement NVS open/load/save**

Validate before saving. Reject invalid config without partially writing values.

- [ ] **Step 2: Ensure token/password are never logged**

Log only whether they are configured.

- [ ] **Step 3: Build ESP32 target**

```bash
pio run -e esp32dev
```

- [ ] **Step 4: Commit**

```bash
git add firmware/esp32/src/config
git commit -m "feat: persist BioVolt device configuration in NVS"
```

---

### Task 5: Add serial provisioning CLI

**Files:**
- Create: `firmware/esp32/src/provisioning/SerialProvisioner.h`
- Create: `firmware/esp32/src/provisioning/SerialProvisioner.cpp`
- Modify: `firmware/esp32/src/main.cpp`
- Modify: `firmware/esp32/README.md`

**Interfaces:**

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
config reset
reboot
```

- [ ] **Step 1: Implement line-buffered parser**

Reject lines longer than 256 bytes and malformed integers.

- [ ] **Step 2: Implement redacted `config show`**

Expected example:

```text
ssid=BioVolt-Hotspot
wifi_password=<configured>
backend_host=192.168.137.1
backend_port=8000
device_id=biovolt-01
cell_id=cell-a
token=<configured>
```

- [ ] **Step 3: Validate before `config save`**

Print the validation message and do not write invalid state.

- [ ] **Step 4: Build and manually verify with serial monitor**

```bash
pio run -e esp32dev -t upload
pio device monitor -b 115200
```

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/src/provisioning firmware/esp32/src/main.cpp firmware/esp32/README.md
git commit -m "feat: provision BioVolt ESP32 configuration over serial"
```

## Module 3.2 Exit Criteria

- [ ] Board wiring has one source of truth.
- [ ] Runtime config is validated.
- [ ] NVS persists configuration across reboot.
- [ ] Local secrets file is ignored.
- [ ] Serial CLI can change laptop/backend identity without reflashing.
- [ ] Token/password never appear in logs.
