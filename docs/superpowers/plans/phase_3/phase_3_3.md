# Phase 3.3: Physical Sensor Acquisition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Acquire real BPV voltage, BPW34 optical signal, temperature, and ambient light every 500 ms while preserving exact Phase 0 null/health semantics and avoiding blocking sensor calls.

**Architecture:** Each physical sensor has a focused driver. `SensorManager` combines their outputs into one `SensorSnapshot`. ADS1115 owns two analog channels, DS18B20 runs asynchronous conversion, BH1750 uses continuous measurement, and the 680 nm probe LED is pulsed only around BPW34 acquisition.

**Tech Stack:** Wire/I2C, Adafruit ADS1X15, OneWire, DallasTemperature, BH1750, FreeRTOS timing primitives.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- ADS1115 address defaults to `0x48`.
- ADS1115 A0 is BPV load-voltage input.
- ADS1115 A1 is the BPW34 optical front-end input.
- Use `GAIN_ONE` unless the real analog front-end requires a documented change.
- ESP32 firmware transmits measured voltage and raw ADC values only. Backend calibration/derived calculations stay in FastAPI.
- DS18B20 must not perform a blocking 12-bit 750 ms conversion inside the 500 ms sensor loop.
- Missing sensor hardware must not prevent remaining sensors from producing telemetry.
- Invalid sensor values become `valid=false`, later serialized as JSON `null`.

---

### Task 1: Implement ADS1115 sampler

**Files:**
- Create: `firmware/esp32/src/sensors/Ads1115Sampler.h`
- Create: `firmware/esp32/src/sensors/Ads1115Sampler.cpp`

**Interfaces:**

```cpp
struct AnalogSample {
  int16_t raw{0};
  float millivolts{0.0F};
  bool valid{false};
};

class Ads1115Sampler {
 public:
  bool begin();
  bool healthy() const;
  AnalogSample readBpv();
  AnalogSample readOptical();
};
```

- [ ] **Step 1: Initialize Wire using `BoardConfig` pins**

Use:

```cpp
Wire.begin(BoardConfig::kI2cSda, BoardConfig::kI2cScl);
```

Initialize ADS1115 at configured address and set `GAIN_ONE`.

- [ ] **Step 2: Add I2C ACK health probe**

Before channel reads, use `Wire.beginTransmission(address)` / `endTransmission()` and mark the ADC unavailable when ACK fails.

- [ ] **Step 3: Convert ADC code to millivolts**

Use the library's `computeVolts(raw) * 1000.0F`. Do not apply `ads1115_offset_mv` in firmware.

- [ ] **Step 4: Build firmware**

```bash
pio run -e esp32dev
```

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/src/sensors/Ads1115Sampler.*
git commit -m "feat: acquire BPV and optical ADC channels"
```

---

### Task 2: Implement asynchronous DS18B20 driver

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

- [ ] **Step 1: Configure 10-bit resolution**

10-bit conversion time is short enough for the 500 ms task cadence. Call `setWaitForConversion(false)`.

- [ ] **Step 2: Implement two-stage polling**

State machine:

```text
IDLE -> requestTemperatures() -> CONVERTING
CONVERTING and conversion interval elapsed -> read temperature -> IDLE
```

Never call `requestTemperatures()` followed by a blocking wait.

- [ ] **Step 3: Reject disconnected/invalid readings**

Treat `DEVICE_DISCONNECTED_C`, non-finite values, and values outside DS18B20's documented -55..125 C range as invalid.

- [ ] **Step 4: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/sensors/TemperatureSensor.*
git commit -m "feat: acquire DS18B20 temperature asynchronously"
```

---

### Task 3: Implement BH1750 continuous light driver

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

Use configured address `0x23` and the already-started I2C bus.

- [ ] **Step 2: Validate reads**

Accept finite values >= 0. A failed/not-ready reading is invalid rather than `0`.

- [ ] **Step 3: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/sensors/LightSensor.*
git commit -m "feat: acquire BioVolt ambient light"
```

---

### Task 4: Implement 680 nm optical probe acquisition

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

- [ ] **Step 1: Configure probe LED output OFF before enabling pin output**

Use GPIO 25 through a proper driver stage.

- [ ] **Step 2: Pulse the 680 nm LED only for measurement**

Sequence:

```text
probe LED ON
wait 20 ms settling time
read ADS1115 A1
probe LED OFF
```

Use `vTaskDelay(pdMS_TO_TICKS(20))`, not `delay(20)`.

- [ ] **Step 3: Define `ledEnabledAtSample` semantics**

Set true only when the A1 sample was actually taken with the probe LED enabled. This is the value later serialized as `optical.led_680_enabled`.

- [ ] **Step 4: Build and commit**

```bash
pio run -e esp32dev
git add firmware/esp32/src/sensors/OpticalProbe.*
git commit -m "feat: sample BPW34 under pulsed 680 nm illumination"
```

---

### Task 5: Implement `SensorManager`

**Files:**
- Create: `firmware/esp32/src/sensors/SensorManager.h`
- Create: `firmware/esp32/src/sensors/SensorManager.cpp`

**Interfaces:**

```cpp
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

class SensorManager {
 public:
  void begin();
  SensorFrame sample(uint64_t nowMs);
};
```

- [ ] **Step 1: Initialize each driver independently**

A missing BH1750 must not stop ADS1115/DS18B20 startup, and vice versa.

- [ ] **Step 2: Populate health rules**

```text
ads1115Ok       = ADC ACK/read path available
bpw34Ok         = ADS1115 optical channel successfully acquired
                 (not a claim of optical calibration validity)
temperatureOk   = latest DS18B20 sample valid
lightSensorOk   = latest BH1750 sample valid
```

- [ ] **Step 3: Populate snapshot validity**

Invalid driver reads keep the corresponding `SensorValue.valid=false`.

- [ ] **Step 4: Build and manually inspect one serial debug dump**

Do not yet format production telemetry. Print a compact diagnostic once per second during bench verification only.

- [ ] **Step 5: Commit**

```bash
git add firmware/esp32/src/sensors
git commit -m "feat: aggregate BioVolt sensor snapshots and health"
```

## Module 3.3 Exit Criteria

- [ ] ADS1115 A0 and A1 can be acquired independently.
- [ ] ADC offset is not applied in firmware.
- [ ] DS18B20 is non-blocking at 500 ms system cadence.
- [ ] BH1750 failure does not stop other sensors.
- [ ] Probe LED is off except around optical acquisition.
- [ ] Invalid sensor readings map cleanly to validity=false/health=false.
- [ ] `bpw34Ok` semantics are documented as acquisition health, not calibration validity.
