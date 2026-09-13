# ESP32 Firmware

Planned owner: ESP32 DevKit V1 using PlatformIO, Arduino Framework, and FreeRTOS.

Responsibilities beginning in the firmware phase:

- raw sensor acquisition
- actuator state
- sensor health
- local safety
- Perturb & Observe control
- sequence and uptime counters
- WebSocket device transport

Scientific derived values remain backend-owned.

Phase 0 contains no firmware runtime code.

Phase 3.1: PlatformIO project bootstrapped. See Task 4 for build commands.

## Build and test

The firmware is built and tested with [PlatformIO](https://platformio.org/).

```bash
# Build the ESP32 target (espressif32 platform, ESP32 DevKit V1).
pio run -e esp32dev

# Run the host-side C++ test suite against `lib/BioVoltCore`.
pio test -e native

# Open a serial monitor against a connected device.
pio device monitor -b 115200
```

## Module boundary (Phase 3.1)

Phase 3.1 contains **no live sensors, networking, or remote control**. The
project is bootstrapped to:

- Compile cleanly for the `esp32dev` target.
- Run a host-side C++ test suite under `[env:native]` (the Unity test
  runner on the host compiler, no ESP32 toolchain required).

Pure protocol/safety/timing code lives under `lib/BioVoltCore/` so the
unit tests can run natively. The headers there (`SensorTypes.h`,
`RuntimeTypes.h`, `Backoff.h`) do not include `Arduino.h` and have no
hardware dependencies. ESP32-only code (drivers, FreeRTOS tasks, Wi-Fi,
WebSocket client) is added in later modules: 3.2 (config/NVS),
3.3 (sensors), 3.4 (actuators + safety), 3.5 (FreeRTOS runtime),
3.6 (telemetry transport), 3.7 (parity), 3.8 (CI + HIL).

`src/main.cpp` initializes Serial and idles `loop()`; later modules
will add FreeRTOS tasks from `setup()`. The default `ActuatorState`
(PWM = 0, mixer off) and `ControlMode::Monitor` reflect the
"firmware starts from safe actuator defaults" constraint.

