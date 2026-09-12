# Phase 3 Overview: Real ESP32 Firmware and Hardware Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the deterministic Python device simulator with a real ESP32 that acquires BioVolt sensors, maintains safe local actuator state, and streams the exact Phase 0 `device-telemetry.v1` contract to the unchanged Phase 1 backend every 500 ms under normal operation.

**Architecture:** The ESP32 is a contract-compatible device client, not a special backend mode. Pure DTO, safety, validation, timing, and telemetry-serialization logic lives in `lib/BioVoltCore` so it is host-testable. ESP32-only sensor, actuator, NVS, serial, FreeRTOS, Wi-Fi, and WebSocket code lives in `src/`. Sensor, control, actuator, provisioning, and telemetry responsibilities run independently so a network stall cannot stop sensing or safety enforcement.

**Tech Stack:** ESP32 DevKit V1 / ESP32-WROOM-32, PlatformIO, Arduino Framework, FreeRTOS, ArduinoJson 6.x, Adafruit ADS1X15, OneWire, DallasTemperature, BH1750, Links2004 WebSockets, ESP32 Preferences/NVS, PlatformIO Unity tests, existing FastAPI/PWA stack.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 0 raw telemetry contract, Phase 1 authenticated `/ws/device` boundary and simulator-to-hardware parity rule, and Phase 2 source-neutral PWA.

## Global Constraints

- Real ESP32 and simulator use the same `WS /ws/device`, auth headers, and `device-telemetry.v1` schema.
- Raw firmware telemetry never contains `current_ua`, `power_uw`, `od680`, biomass, carbon, cumulative energy, or wall-clock server time.
- FastAPI remains the owner of scientific derivations, persistence, cumulative energy, and dashboard fanout.
- Normal sensing and telemetry cadence is 500 ms, while backend processing tolerates real Wi-Fi jitter and dropped frames.
- Sensor acquisition and actuator safety continue if Wi-Fi, FastAPI, or the PWA is unavailable.
- Phase 3 has no flash telemetry queue and makes no lossless-backfill claim. Unsent frames are discarded and sequence gaps expose missing observation periods.
- `optimizer_direction` is always `0` in Phase 3. Perturb & Observe is deferred.
- Phase 3 always boots in `monitor` mode with grow-light PWM `0` and mixer OFF. No stored runtime setting may bypass these boot-safe actuator states.
- Remote actuation, experiment lifecycle, command acknowledgements, adaptive optimization, calibration-wizard writes, and operator PIN workflows are outside Phase 3.
- Active runtime network/device configuration is immutable for a boot session. Serial provisioning edits a draft configuration, saves it to NVS, and applies it after reboot.
- Secrets are never committed and never printed in clear text.
- Invalid/missing sensors serialize as protocol `null` plus false health flags, never fake zero measurements.
- GPIO outputs drive suitable MOSFET/relay/driver stages only. Loads are never powered directly from ESP32 GPIO.

---

## Recommended Board Mapping

All defaults live in one `BoardConfig.h` and may be changed only after wiring review:

```text
I2C SDA              GPIO 21
I2C SCL              GPIO 22
DS18B20 data         GPIO 19
680 nm probe LED     GPIO 25
Grow LED PWM         GPIO 26
Mixer driver         GPIO 27
ADS1115 address      0x48
BH1750 address       0x23
ADS1115 A0           BPV load-voltage channel
ADS1115 A1           BPW34 optical receiver channel
```

Hardware requirements:
- DS18B20 data uses the normal pull-up to 3.3 V.
- Grow LED, mixer, and 680 nm probe LED use external driver stages.
- ADS1115/BPW34 front-end input ranges are verified before power-up.
- Required grounds and supply rails are documented in `docs/hardware/esp32-wiring.md` before HIL acceptance.

---

## Module Map

### 3.1 PlatformIO Firmware Foundation and Testable Core
`docs/superpowers/plans/phase_3/phase_3_1.md`

Produces PlatformIO `esp32dev` and `native` environments, pure DTOs, safe defaults, and deterministic reconnect helpers.

### 3.2 Runtime Configuration, NVS, Secrets, and Serial Provisioning
`docs/superpowers/plans/phase_3/phase_3_2.md`

Produces board constants, host-testable `RuntimeConfig`, one versioned NVS config blob, ignored local secret fallback, redacted serial provisioning, and safe status diagnostics.

### 3.3 Physical Sensor Acquisition
`docs/superpowers/plans/phase_3/phase_3_3.md`

Produces ADS1115 BPV/BPW34 acquisition, asynchronous DS18B20, BH1750, pulsed 680 nm probe acquisition, and shared core `SensorFrame` health/null semantics.

### 3.4 Actuator Drivers and Phase 3 Safety Baseline
`docs/superpowers/plans/phase_3/phase_3_4.md`

Produces boot-safe PWM/mixer drivers, host-tested safety policy, mixer runtime/cooldown enforcement, and non-adaptive Monitor baseline.

### 3.5 FreeRTOS Runtime, State Exchange, Task Isolation, and Provisioning Task
`docs/superpowers/plans/phase_3/phase_3_5.md`

Produces SensorTask, ControlTask, ActuatorTask, low-priority ProvisioningTask, one-slot actuator queue, and thread-safe runtime snapshots.

### 3.6 Device Telemetry Serialization, Wi-Fi, and WebSocket Transport
`docs/superpowers/plans/phase_3/phase_3_6.md`

Produces host-tested core telemetry serializer, monotonic sequence/uptime, non-blocking Wi-Fi, authenticated `/ws/device`, bounded reconnect, and live-resume/no-replay behavior.

### 3.7 Real-Hardware Backend/PWA Parity and Telemetry-Gap Safety
`docs/superpowers/plans/phase_3/phase_3_7.md`

Produces source-neutral continuity tracking, non-integrating energy anchors across sequence gaps, simulator-off/ESP32-on parity, and unchanged PWA rendering.

### 3.8 Hardware-in-the-Loop Soak, CI, Wiring Docs, and Phase Acceptance
`docs/superpowers/plans/phase_3/phase_3_8.md`

Produces firmware CI, wiring/pre-power docs, sensor fault tests, reconnect acceptance, and 30-minute real-device soak evidence.

---

## Mandatory Dependency Order

```text
Phase 0/1/2 interfaces ready
        |
        v
3.1 PlatformIO + pure core
        |
        v
3.2 Configuration + provisioning
        |
        v
3.3 Physical sensors
        |
        v
3.4 Actuator safety
        |
        v
3.5 FreeRTOS task isolation
        |
        v
3.6 Telemetry + Wi-Fi + WebSocket
        |
        v
3.7 Hardware parity + gap-safe energy
        |
        v
3.8 HIL soak + CI + acceptance
        |
        v
Phase 3 complete
```

## Runtime Data Flow

```text
ADS1115 A0/A1 + DS18B20 + BH1750
                |
                v
          SensorTask 500 ms
                |
                v
         RuntimeStateStore
            /          \
           v            v
 ControlTask 500 ms   TelemetryTask
           |            |
           v            v
 actuator queue    device-telemetry.v1
           |            |
           v            v
    ActuatorTask   authenticated /ws/device
                        |
                        v
                     FastAPI
                        |
                        v
                  unchanged PWA

Serial USB
   |
   v
ProvisioningTask -> draft config -> NVS config_v1 -> reboot required
```

Phase 3 control state is exact:

```text
mode = monitor
optimizer_direction = 0
grow_led_pwm = 0
mixer_on = false
```

No P&O claim is made in this phase.

---

## Planned Firmware Structure

```text
firmware/esp32/
├── platformio.ini
├── README.md
├── include/
│   ├── BoardConfig.h
│   ├── BuildSecrets.example.h
│   └── BuildSecrets.h                 # ignored locally
├── lib/
│   └── BioVoltCore/
│       ├── SensorTypes.h              # SensorValue, AnalogSample, SensorSnapshot, SensorHealth, SensorFrame
│       ├── RuntimeTypes.h             # actuator/control/runtime snapshot DTOs
│       ├── RuntimeConfig.h
│       ├── ConfigValidation.h
│       ├── Backoff.h
│       ├── SafetyPolicy.h
│       ├── ControlBaseline.h
│       ├── TelemetryModel.h
│       ├── TelemetrySerializer.h
│       └── TelemetrySerializer.cpp
├── src/
│   ├── main.cpp
│   ├── config/ConfigStore.h/.cpp
│   ├── provisioning/SerialProvisioner.h/.cpp
│   ├── sensors/
│   │   ├── Ads1115Sampler.h/.cpp
│   │   ├── OpticalProbe.h/.cpp
│   │   ├── TemperatureSensor.h/.cpp
│   │   ├── LightSensor.h/.cpp
│   │   └── SensorManager.h/.cpp
│   ├── actuators/
│   │   ├── GrowLightDriver.h/.cpp
│   │   ├── MixerDriver.h/.cpp
│   │   └── ActuatorController.h/.cpp
│   ├── runtime/
│   │   ├── RuntimeStateStore.h/.cpp
│   │   ├── SensorTask.h/.cpp
│   │   ├── ControlTask.h/.cpp
│   │   ├── ActuatorTask.h/.cpp
│   │   └── ProvisioningTask.h/.cpp
│   ├── telemetry/TelemetryTask.h/.cpp
│   └── network/
│       ├── NetworkManager.h/.cpp
│       └── DeviceWebSocket.h/.cpp
└── test/
    ├── test_core_types/
    ├── test_core_backoff/
    ├── test_core_safety/
    ├── test_control_baseline/
    ├── test_config_validation/
    └── test_telemetry_model/
```

Anything executed by the `native` test environment must live under `lib/BioVoltCore`, not under ESP32-only `src/`.

---

## Raw Telemetry Rules

A real-device frame contains exactly the Phase 0 groups and fields:

```text
schema_version, device_id, sequence, uptime_ms, cell_id

electrical: bpv_voltage_mv, bpv_adc_raw
optical: bpw34_raw, bpw34_voltage_mv, led_680_enabled
environment: temperature_c, lux
actuators: grow_led_pwm, mixer_on
control: mode, optimizer_direction
health: ads1115_ok, bpw34_ok, temperature_ok, light_sensor_ok
```

`led_680_enabled` is the probe LED state **at the instant the BPW34 sample was acquired**, not a continuous-output claim. `bpw34_ok` means the optical acquisition path was successfully read; it does not assert valid calibration or biological interpretation.

---

## Network Loss Policy

```text
sensing continues
control/safety continues
actuator timeout enforcement continues
serial provisioning remains available
no flash telemetry queue
no stale-frame replay
sequence advances at scheduled telemetry ticks
Wi-Fi/WebSocket reconnect with bounded backoff
live state resumes after reconnect
```

A backend continuity tracker in Module 3.7 treats sequence gaps as unobserved intervals and does not integrate energy across them.

---

## Planned Commit Sequence

1. `chore: bootstrap BioVolt ESP32 PlatformIO firmware`
2. `feat: add BioVolt device configuration and provisioning`
3. `feat: acquire BioVolt physical sensors on ESP32`
4. `feat: add ESP32 actuator safety baseline`
5. `feat: run BioVolt firmware with isolated FreeRTOS tasks`
6. `feat: stream real ESP32 telemetry to BioVolt backend`
7. `fix: treat real telemetry gaps as energy discontinuities`
8. `test: add ESP32 hardware soak CI and acceptance docs`

## Phase 3 Exit Criteria

- [ ] ESP32 firmware compiles reproducibly and native core tests pass.
- [ ] Local secrets are ignored and redacted from logs.
- [ ] Runtime config can be provisioned without editing drivers; saved changes apply after reboot.
- [ ] ESP32 always boots grow LED PWM 0 and mixer OFF.
- [ ] ADS1115 A0/A1 produce raw count and mV telemetry when connected.
- [ ] DS18B20 is asynchronous and does not stall the 500 ms sensor schedule.
- [ ] BH1750 returns lux or explicit null/false health.
- [ ] Missing sensors do not stop remaining sensing/network tasks.
- [ ] SensorTask and ControlTask run approximately every 500 ms without cumulative `delay(500)` drift.
- [ ] ActuatorTask enforces PWM bounds, mixer max runtime, and cooldown.
- [ ] Provisioning remains usable after the main FreeRTOS runtime starts.
- [ ] Real serializer matches `device-telemetry.v1` and contains no backend-derived values.
- [ ] Uptime uses monotonic 64-bit ESP32 time; sequence advances once per scheduled frame.
- [ ] Wi-Fi/backend outages do not stop sensing/safety and do not require ESP32 reboot.
- [ ] Simulator can be stopped and real ESP32 appears through unchanged `/ws/device`.
- [ ] `/api/system/status` shows the configured real device ID.
- [ ] Existing Phase 2 PWA displays real hardware telemetry without a source-specific rebuild.
- [ ] Dropped telemetry gaps do not cause FastAPI to integrate energy across unobserved intervals.
- [ ] 30-minute real-device soak passes without unexpected reset, runaway actuator, backend crash, or progressive memory collapse.
- [ ] Phase 0 contract, Phase 1 backend, Phase 2 frontend, and firmware regression suites remain green.

## Handoff to Phase 4

Phase 4 should add the experiment/control command substrate on top of this proven physical path: backend experiment lifecycle, `device-command.v1` delivery plus acknowledgement, Passive/Manual workflows, and operator-protected controls. Adaptive P&O remains later until command delivery and experiments are reliable.
