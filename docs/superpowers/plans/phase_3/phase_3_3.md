# Phase 3.3: Physical Sensor Acquisition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Acquire real BPV voltage, BPW34 optical signal, temperature, and ambient light on a 500 ms system schedule while preserving exact Phase 0 null/health semantics and avoiding blocking sensor calls.

**Architecture:** Shared sensor DTOs live in `lib/BioVoltCore/SensorTypes.h` so telemetry serialization can be tested natively without ESP32 drivers. Hardware-specific drivers live under `src/sensors`. `SensorManager` combines the driver results into the core `SensorFrame`. ADS1115 owns the BPV and optical analog channels, DS18B20 conversion is asynchronous, BH1750 is continuous, and the 680 nm probe LED is pulsed only around BPW34 acquisition.

**Tech Stack:** Wire/I2C, Adafruit ADS1X15, OneWire, DallasTemperature, BH1750, FreeRTOS timing primitives.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- ADS1115 address defaults to `0x48`; A0 is BPV, A1 is BPW34 front-end.
- Use `GAIN_ONE` unless the actual analog front-end requires a separately documented gain change.
- Firmware sends measured voltage/raw ADC only; calibration and derived science remain backend-owned.
- DS18B20 must not perform a blocking 12-bit 750 ms conversion in the 500 ms sensor loop.
- Missing hardware must not prevent remaining sensors from operating.
- Invalid readings become `SensorValue.valid=false`, later serialized as JSON `null` with the matching health flag false.
- Shared DTOs required by native tests must stay under `lib/BioVoltCore`, not ESP32-only `src/`.

---

### Task 1: Complete shared sensor DTOs in BioVoltCore

**Files:**
- Modify: `firmware/esp32/lib/BioVoltCore/SensorTypes.h`
- Modify/Create: `firmware/esp32/test/test_core_types/test_main.cpp`

**Interfaces:**

```cpp
template <typename T>
struct SensorValue {
  T value{};
  bool valid{false};
};

struct AnalogSample {
  int16_t raw{0};
  float millivolts{0.0F};
  bool valid{false};
};

struct SensorSnapshot {
  SensorValue<float> bpvVoltageMv;
  SensorValue<int16_t> bpvAdcRaw;
  SensorValue<float> bpw34VoltageMv;
  SensorValue<int16_t> bpw34Raw;
  bool led680EnabledAtSample{false};
  SensorValue<float> temperatureC;
  SensorValue<float> lux;
};

struct SensorHealth {
  bool ads1115Ok{false};
  bool bpw34Ok{false};
  bool temperatureOk{false};
  bool lightSensorOk{false};
};

struct SensorFrame {
  SensorSnapshot snapshot;
  SensorHealth health;
};
```

- [ ] **Step 1: Add failing native tests for default invalid/false state**

```bash
cd firmware/esp32
pio test -e native -f test_core_types
```

- [ ] **Step 2: Implement DTOs without Arduino includes**

Use `<cstdint>` only.

- [ ] **Step 3: Re-run native test**

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add lib/BioVoltCore/SensorTypes.h test/test_core_types
git commit -m "feat: define shared BioVolt sensor frame DTOs"
```

---

### Task 2: Implement ADS1115 sampler

**Files:**
- Create: `firmware/esp32/src/sensors/Ads1115Sampler.h`
- Create: `firmware/esp32/src/sensors/Ads1115Sampler.cpp`

**Interfaces:**

```cpp
class Ads1115Sampler {
 public:
  bool begin();
  bool healthy() const;
  AnalogSample readBpv();
  AnalogSample readOptical();
};
```

- [ ] **Step 1: Initialize the shared I2C bus from BoardConfig**

```cpp
Wire.begin(BoardConfig::kI2cSda, BoardConfig::kI2cScl);
```

Initialize ADS1115 at `BoardConfig::kAds1115Address` and select `GAIN_ONE`.

- [ ] **Step 2: Add I2C ACK health probe**

Use `Wire.beginTransmission(address)` plus `endTransmission()`. A missing ADC yields invalid channel samples rather than blocking/rebooting.

- [ ] **Step 3: Convert code to mV**

Use:

```cpp
sample.millivolts = ads.computeVolts(raw) * 1000.0F;
```

Do not apply ADS offset or load-resistor calculations in firmware.

- [ ] **Step 4: Build**

```bash
pio run -e esp32dev
```

- [ ] **Step 5: Commit**

```bash
git add src/sensors/Ads1115Sampler.*
git commit -m "feat: acquire BPV and optical ADC channels"
```

---

### Task 3: Implement asynchronous DS18B20 driver

**Files:**
- Create: `firmware/esp32/src/sensors/TemperatureSensor.h`
- Create: `firmware/esp32/src/sensors/TemperatureSensor.cpp`

**Interfaces:**

```cpp
class TemperatureSensor {
 public:
  bool begin();
  void poll(uint64_t nowMs);
  SensorValue<float> latest() const;
};
```

- [ ] **Step 1: Configure 10-bit resolution and asynchronous conversion**

Call:

```cpp
sensors.setResolution(10);
sensors.setWaitForConversion(false);
```

- [ ] **Step 2: Implement state machine**

```text
IDLE -> requestTemperatures() -> CONVERTING
CONVERTING after configured 10-bit conversion interval -> read -> IDLE
```

Do not block waiting for conversion.

- [ ] **Step 3: Reject invalid readings**

`DEVICE_DISCONNECTED_C`, non-finite values, and values outside -55..125 C are invalid.

- [ ] **Step 4: Build and commit**

```bash
pio run -e esp32dev
git add src/sensors/TemperatureSensor.*
git commit -m "feat: acquire DS18B20 temperature asynchronously"
```

---

### Task 4: Implement BH1750 continuous light driver

**Files:**
- Create: `firmware/esp32/src/sensors/LightSensor.h`
- Create: `firmware/esp32/src/sensors/LightSensor.cpp`

**Interfaces:**

```cpp
class LightSensor {
 public:
  bool begin();
  SensorValue<float> readLux();
};
```

- [ ] **Step 1: Initialize continuous high-resolution mode**

Use `BoardConfig::kBh1750Address` on the existing I2C bus.

- [ ] **Step 2: Validate reads**

Only finite `lux >= 0` is valid. Not-ready/failure is invalid, not `0`.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add src/sensors/LightSensor.*
git commit -m "feat: acquire BioVolt ambient light"
```

---

### Task 5: Implement pulsed 680 nm optical probe

**Files:**
- Create: `firmware/esp32/src/sensors/OpticalProbe.h`
- Create: `firmware/esp32/src/sensors/OpticalProbe.cpp`

**Interfaces:**

```cpp
struct OpticalSample {
  AnalogSample receiver;
  bool ledEnabledAtSample{false};
};

class OpticalProbe {
 public:
  explicit OpticalProbe(Ads1115Sampler& adc);
  void begin();
  OpticalSample sample();
};
```

- [ ] **Step 1: Force probe LED OFF before configuring output**

The pin drives an external transistor/driver, never the LED load directly.

- [ ] **Step 2: Pulse only around measurement**

```text
probe LED ON
vTaskDelay(20 ms settling)
read ADS1115 A1
record ledEnabledAtSample=true only for successful sample
probe LED OFF unconditionally
```

Use a guard/finally-equivalent control structure so error returns cannot leave the probe LED ON.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add src/sensors/OpticalProbe.*
git commit -m "feat: sample BPW34 under pulsed 680 nm illumination"
```

---

### Task 6: Implement SensorManager

**Files:**
- Create: `firmware/esp32/src/sensors/SensorManager.h`
- Create: `firmware/esp32/src/sensors/SensorManager.cpp`

**Interfaces:**

```cpp
class SensorManager {
 public:
  void begin();
  SensorFrame sample(uint64_t nowMs);
};
```

- [ ] **Step 1: Initialize each physical driver independently**

A missing BH1750 must not prevent ADS1115 or DS18B20 startup, and vice versa.

- [ ] **Step 2: Define exact health semantics**

```text
ads1115Ok      = ADS1115 acquisition path available
bpw34Ok        = optical A1 acquisition succeeded with probe measurement
                 not a claim of optical calibration validity
temperatureOk  = latest DS18B20 value valid
lightSensorOk  = current BH1750 read valid
```

- [ ] **Step 3: Copy raw measured values into SensorFrame**

No current, power, OD680, biomass, CO2, energy, or calibration correction is computed here.

- [ ] **Step 4: Add bench-only diagnostic behind compile flag**

At most once per second, print validity/raw readings. Production/default build must not flood serial every 500 ms.

- [ ] **Step 5: Build and commit**

```bash
pio run -e esp32dev
git add src/sensors
git commit -m "feat: aggregate BioVolt sensor snapshots and health"
```

## Module 3.3 Exit Criteria

- [ ] Shared SensorFrame types are native-testable.
- [ ] ADS1115 A0/A1 can fail independently without crashing firmware.
- [ ] ADC offset/current/power are not computed in firmware.
- [ ] DS18B20 conversion does not block 500 ms schedule.
- [ ] BH1750 failure does not stop other sensors.
- [ ] Probe LED is guaranteed OFF outside measurement pulse.
- [ ] Invalid sensor reads map to validity=false and later null/false protocol values.
- [ ] `bpw34Ok` is acquisition health only, not calibration validity.
