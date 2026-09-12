# Phase 3 Overview: Real ESP32 Firmware and Hardware Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the deterministic Python device simulator with a real ESP32 that acquires BioVolt sensors, maintains safe local actuator state, and streams the exact Phase 0 `device-telemetry.v1` contract to the unchanged Phase 1 backend every 500 ms under normal operation.

**Architecture:** The ESP32 is implemented as a contract-compatible device client, not as a special backend mode. Sensor acquisition, safety/control scaffolding, actuator output, and telemetry/networking are separated into FreeRTOS tasks that exchange typed snapshots and queues. The backend and PWA remain source-neutral, so switching from simulator to ESP32 is an operational change only.

**Tech Stack:** ESP32 DevKit V1 / ESP32-WROOM-32, PlatformIO, Arduino Framework, FreeRTOS, ArduinoJson 6.x, Adafruit ADS1X15, OneWire, DallasTemperature, BH1750, Links2004 WebSockets, ESP32 Preferences/NVS, PlatformIO Unity tests, existing FastAPI/PWA integration stack.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 0 raw telemetry contract, Phase 1 authenticated `/ws/device` device boundary, Phase 1 simulator-to-hardware parity rule, and Phase 2 source-neutral PWA.

## Global Constraints

- The real ESP32 must use the same `WS /ws/device` endpoint used by the simulator.
- The real ESP32 must use the same authentication headers: `X-BioVolt-Device-ID` and `Authorization: Bearer <shared-token>`.
- The ESP32 must emit the exact Phase 0 `device-telemetry.v1` shape.
- Raw firmware telemetry must never include `current_ua`, `power_uw`, `od680`, biomass, carbon, cumulative energy, or wall-clock server time.
- FastAPI remains the owner of current, power, OD680, biomass, carbon, energy, persistence, and dashboard fanout.
- Normal sensor and telemetry cadence is 500 ms, but the backend must tolerate real network jitter and dropped frames.
- Sensor acquisition and actuator safety must continue if Wi-Fi, FastAPI, or the PWA is unavailable.
- No telemetry replay/backfill is claimed in Phase 3. The device resumes live telemetry after reconnect and sequence gaps reveal missing frames.
- `optimizer_direction` remains `0` in Phase 3. Perturb & Observe optimization is deliberately deferred to a later control phase.
- Phase 3 boots in `monitor` mode with grow LED PWM `0` and mixer OFF unless an explicitly stored safe local configuration says otherwise.
- Manual remote actuation, experiment lifecycle, adaptive optimization, calibration wizard writes, and operator PIN workflows remain out of Phase 3.
- Secrets must not be committed or printed in serial logs.
- Invalid/missing sensors produce protocol `null` values plus false health flags, never fake zero measurements.
- GPIO outputs control MOSFET/relay/driver stages only. Grow lights, mixer motors/pumps, and probe LEDs are never powered directly from ESP32 GPIO pins.

---

## Recommended Board Mapping

The plan uses these defaults in one compile-time board configuration file so wiring can be changed without touching driver logic:

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

Hardware notes:
- DS18B20 data requires the normal pull-up resistor to 3.3 V.
- Grow LED, mixer, and 680 nm LED outputs must drive suitable transistor/MOSFET/relay stages.
- Final wiring must be verified against the actual prototype before power is applied.
- Pin/address values live in `BoardConfig.h`, not duplicated across drivers.

---

## Module Map

### Module 3.1: PlatformIO Firmware Foundation and Testable Core
Plan: `docs/superpowers/plans/phase_3/phase_3_1.md`

Produces:
- PlatformIO ESP32 project
- native host-test environment for pure firmware logic
- firmware boot skeleton
- typed sensor/actuator/control DTOs
- timing/backoff helpers
- compile/test commands

### Module 3.2: Runtime Configuration, NVS, Secrets, and Serial Provisioning
Plan: `docs/superpowers/plans/phase_3/phase_3_2.md`

Produces:
- board configuration constants
- runtime device/network configuration
- Preferences/NVS persistence
- ignored local secrets fallback
- safe serial configuration CLI with secret redaction

### Module 3.3: Physical Sensor Acquisition
Plan: `docs/superpowers/plans/phase_3/phase_3_3.md`

Produces:
- ADS1115 BPV acquisition
- BPW34 optical acquisition with 680 nm probe pulse
- asynchronous DS18B20 temperature acquisition
- BH1750 light acquisition
- explicit health/null semantics
- 500 ms `SensorSnapshot`

### Module 3.4: Actuator Drivers and Phase 3 Safety Baseline
Plan: `docs/superpowers/plans/phase_3/phase_3_4.md`

Produces:
- grow-light PWM driver
- mixer driver
- hard boot-safe outputs
- mixer max-runtime/cooldown enforcement
- PWM clamping
- `monitor`-mode baseline with optimizer disabled

### Module 3.5: FreeRTOS Runtime, State Exchange, and Task Isolation
Plan: `docs/superpowers/plans/phase_3/phase_3_5.md`

Produces:
- `SensorTask`
- `ControlTask`
- `ActuatorTask`
- shared runtime-state store
- one-slot actuator command queue
- cadence tests/diagnostics

### Module 3.6: Device Telemetry Serialization, Wi-Fi, and WebSocket Transport
Plan: `docs/superpowers/plans/phase_3/phase_3_6.md`

Produces:
- exact `device-telemetry.v1` serializer
- sequence/uptime handling
- Wi-Fi reconnect
- authenticated `/ws/device` transport
- bounded WebSocket reconnect backoff
- no-replay live-resume behavior
- source-neutral backend compatibility

### Module 3.7: Real-Hardware Backend/PWA Parity and Telemetry-Gap Safety
Plan: `docs/superpowers/plans/phase_3/phase_3_7.md`

Produces:
- simulator-off / ESP32-on parity acceptance
- backend regression for dropped-sequence energy discontinuities
- real hardware visibility through `/api/system/status`
- unchanged PWA live rendering
- reconnect and sensor-fault integration checks

### Module 3.8: Hardware-in-the-Loop Soak, CI, Wiring Docs, and Phase Acceptance
Plan: `docs/superpowers/plans/phase_3/phase_3_8.md`

Produces:
- PlatformIO firmware CI
- HIL smoke checklist
- 30-minute real-device soak procedure
- wiring/configuration documentation
- phase acceptance evidence

---

## Mandatory Dependency Order

```text
Phase 0 / Phase 1 / Phase 2 contracts ready
                |
                v
3.1 PlatformIO + testable core
                |
                v
3.2 Runtime configuration + provisioning
                |
                v
3.3 Physical sensor acquisition
                |
                v
3.4 Actuator safety baseline
                |
                v
3.5 FreeRTOS runtime/task isolation
                |
                v
3.6 Wi-Fi + device telemetry WebSocket
                |
                v
3.7 Hardware parity + telemetry-gap safety
                |
                v
3.8 HIL soak + CI + acceptance
                |
                v
Phase 3 complete
```

---

## Firmware Runtime Data Flow

```text
ADS1115 A0  BPV voltage ─┐
ADS1115 A1  BPW34       ─┤
DS18B20     temperature ─┤
BH1750      lux         ─┘
            |
            v
       SensorTask 500 ms
            |
            v
       RuntimeState
            |
      +-----+------------------+
      |                        |
      v                        v
 ControlTask 500 ms      TelemetryTask
      |                        |
      v                        |
 Actuator queue                |
      |                        |
      v                        |
 ActuatorTask                  |
                               v
                     device-telemetry.v1
                               |
                               v
                   authenticated /ws/device
                               |
                               v
                            FastAPI
                               |
                        unchanged backend
                               |
                               v
                         React PWA
```

Phase 3 control behavior is intentionally conservative:

```text
mode = monitor
optimizer_direction = 0
grow_led_pwm = safe configured value, default 0
mixer_on = false unless locally requested through tested safety layer
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
│   └── BuildSecrets.h              # ignored locally
├── lib/
│   └── BioVoltCore/
│       ├── SensorTypes.h
│       ├── RuntimeTypes.h
│       ├── Backoff.h
│       ├── SafetyPolicy.h
│       └── TelemetryModel.h
├── src/
│   ├── main.cpp
│   ├── config/
│   │   ├── RuntimeConfig.h
│   │   ├── ConfigStore.h
│   │   └── ConfigStore.cpp
│   ├── provisioning/
│   │   ├── SerialProvisioner.h
│   │   └── SerialProvisioner.cpp
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
│   │   └── ActuatorTask.h/.cpp
│   ├── telemetry/
│   │   ├── TelemetrySerializer.h/.cpp
│   │   └── TelemetryTask.h/.cpp
│   └── network/
│       ├── NetworkManager.h/.cpp
│       └── DeviceWebSocket.h/.cpp
└── test/
    ├── test_core_backoff/
    ├── test_core_safety/
    ├── test_telemetry_model/
    └── test_config_validation/
```

---

## Phase 3 Telemetry Rules

A normal real-device frame must contain exactly:

```text
schema_version
device_id
sequence
uptime_ms
cell_id

electrical
  bpv_voltage_mv
  bpv_adc_raw

optical
  bpw34_raw
  bpw34_voltage_mv
  led_680_enabled

environment
  temperature_c
  lux

actuators
  grow_led_pwm
  mixer_on

control
  mode
  optimizer_direction

health
  ads1115_ok
  bpw34_ok
  temperature_ok
  light_sensor_ok
```

The 680 nm flag means **the probe LED state at the instant the BPW34 sample was acquired**. It is not a claim that the probe LED stays on continuously after acquisition.

`bpw34_ok` means the optical acquisition path/channel was successfully read. It does not prove the optical calibration is valid and does not itself prove the photodiode is biologically meaningful.

---

## Network Loss Policy

During Wi-Fi/backend outage:

```text
Sensors continue
Safety/control scaffolding continues
Actuator safety continues
No flash telemetry queue is written
No old frames are replayed later
Sequence continues advancing at telemetry ticks
WebSocket reconnect uses bounded backoff
Live transmission resumes on reconnect
```

This intentionally favors system safety and protocol simplicity over pretending Phase 3 has lossless logging. Sequence gaps allow FastAPI to identify missing telemetry periods.

---

## Planned Commit Sequence

1. `chore: bootstrap BioVolt ESP32 PlatformIO firmware`
2. `feat: add BioVolt device configuration and provisioning`
3. `feat: acquire BioVolt physical sensors on ESP32`
4. `feat: add ESP32 actuator safety baseline`
5. `feat: run BioVolt firmware with isolated FreeRTOS tasks`
6. `feat: stream real ESP32 telemetry to BioVolt backend`
7. `test: enforce real hardware telemetry continuity semantics`
8. `test: add ESP32 hardware soak CI and acceptance docs`

Each implementation checkpoint must pass every test introduced so far before continuing.

---

## Phase 3 Exit Criteria

- [ ] ESP32 firmware compiles reproducibly with PlatformIO.
- [ ] Local secrets are ignored and never printed.
- [ ] Device identity, cell identity, Wi-Fi, backend target, and token can be configured without editing driver code.
- [ ] ESP32 boots with grow-light and mixer outputs in safe states.
- [ ] ADS1115 A0 produces BPV raw count and millivolt telemetry.
- [ ] ADS1115 A1 produces BPW34 raw count and millivolt telemetry under a 680 nm probe pulse.
- [ ] DS18B20 acquisition does not block the 500 ms task cycle with a 750 ms conversion.
- [ ] BH1750 provides lux or explicit null/false health.
- [ ] Missing sensors do not prevent remaining sensors/network from operating.
- [ ] SensorTask cadence is approximately 500 ms without `delay(500)` drift accumulation.
- [ ] ControlTask runs separately and keeps `optimizer_direction=0` in Phase 3.
- [ ] ActuatorTask enforces PWM bounds, mixer max runtime, and mixer cooldown.
- [ ] Real firmware serializer matches `device-telemetry.v1` and contains no backend-derived values.
- [ ] Uptime uses a monotonic 64-bit ESP32 time source.
- [ ] Sequence advances once per scheduled telemetry frame.
- [ ] Wi-Fi/backend outages do not stop sensing/safety tasks.
- [ ] Device reconnects without reboot after backend/Wi-Fi recovery.
- [ ] Simulator can be stopped and real ESP32 appears through the unchanged `/ws/device` path.
- [ ] `/api/system/status` shows the real device ID.
- [ ] Existing Phase 2 PWA displays real hardware telemetry without a source-specific frontend rebuild.
- [ ] A dropped telemetry gap does not cause FastAPI to integrate energy across an unobserved interval.
- [ ] 30-minute real-device soak passes without firmware reset, runaway actuator, or backend crash.
- [ ] Phase 0 contract tests, Phase 1 backend tests, Phase 2 frontend tests, and firmware compile/tests remain green.

## Handoff to Phase 4

Phase 4 should add the **experiment/control command path** on top of the proven physical device: backend experiment lifecycle, `device-command.v1` delivery/acknowledgement, Passive/Manual operating workflows, and operator-protected controls. Adaptive P&O remains a later phase until the command and experiment substrate is reliable.
