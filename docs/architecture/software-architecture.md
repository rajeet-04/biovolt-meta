# BioVolt Software Architecture

**Project:** BioVolt: Adaptive Living Power Cell  
**Event:** MetaMorph 2.0  
**Team:** Team Rocket  
**Status:** Approved architecture baseline

## Objective

BioVolt uses an **offline-first embedded + laptop architecture**. The ESP32 owns physical sensing, fast safety logic, actuator control, and the local Perturb & Observe control loop. A laptop runs FastAPI, SQLite, the React PWA, Nginx, and optional Cloudflared exposure.

The design must work without venue internet.

## Approved stack

### ESP32 firmware

- ESP32 DevKit V1 / ESP32-WROOM-32
- PlatformIO
- Arduino Framework
- Native ESP32 FreeRTOS tasks
- ArduinoJson
- ADS1115 library
- OneWire + DallasTemperature
- BH1750 library
- WebSocket client
- Preferences / NVS

### Laptop backend

- Python
- FastAPI
- Uvicorn
- SQLite
- CSV export
- Persistent WebSocket for ESP32 telemetry and commands
- REST API for experiments, calibration, history, exports, and health

### PWA frontend

- React
- TypeScript
- Vite
- vite-plugin-pwa
- Tailwind CSS
- Recharts
- Zustand
- Dexie + IndexedDB

### Deployment

- Docker Compose
- Nginx serves the production PWA and proxies `/api/*` and `/ws/*`
- Cloudflared is optional and never required for the local demo

## Runtime ownership

### ESP32 owns

- ADC acquisition
- BPV terminal/load voltage acquisition
- BPW34 optical receiver acquisition
- DS18B20 temperature acquisition
- BH1750 light acquisition
- LED PWM state
- mixer state
- local sensor-health flags
- fast safety rules
- Perturb & Observe actuator decisions
- sequence counter
- uptime counter

### FastAPI owns

- server timestamp
- current calculation from measured voltage and configured load resistance
- power calculation
- OD680 calculation from BPW34 raw readings and calibration references
- biomass concentration calculation from the selected calibration profile
- reactor biomass mass
- biomass delta from experiment baseline
- estimated CO2 biofixed into biomass
- cumulative energy
- experiment lifecycle
- calibration profiles
- persistence
- A/B analytics

### React PWA owns

- visualization
- operator interaction
- experiment setup UI
- calibration wizard UI
- charting
- cached display state

The PWA must not independently recalculate scientific values that FastAPI already owns.

## Scientific data chain

### Electrical

```text
BPV cell
  -> known precision load resistor
  -> ADS1115 measures voltage
  -> FastAPI calculates I = V / R
  -> FastAPI calculates P = V^2 / R
  -> FastAPI integrates power over time for cumulative energy
```

Current is therefore a **derived quantity** in the low-cost BioVolt architecture, not a directly measured raw sensor value.

### Optical density and biomass

```text
680 nm LED
  -> algae culture
  -> BPW34 photodiode
  -> ADC reading
  -> dark correction + blank-medium reference
  -> OD680
  -> calibration curve
  -> dry biomass concentration
  -> biomass gain
  -> estimated CO2 biofixed into biomass
```

OD680 is calculated as:

```text
OD680 = -log10((I_sample - I_dark) / (I_blank - I_dark))
```

OD680 is a **derived optical metric**, not a sensor model or directly measured hardware field.

A biomass calibration profile is required before converting OD680 to `g/L`.

The dashboard wording must be **Estimated CO2 biofixed into biomass**, not permanent sequestration and not direct room-air CO2 removal unless a real CO2 sensor is later added.

## Control architecture

The ESP32 runs the local safety layer and Perturb & Observe control. FastAPI orchestrates experiments and sends higher-level setpoints.

The ESP32 continues safe operation if the laptop disconnects.

Approved experiment modes:

- `monitor`
- `passive`
- `adaptive`
- `manual`

## Telemetry cadence

- ESP32 sensor sampling: 500 ms
- ESP32 control loop: 500 ms
- live PWA telemetry: 500 ms
- SQLite persistence: 1 s
- long-duration chart aggregation: 5 to 10 s

## Security baseline

- ESP32 authenticates with a device ID and shared API token
- operator control actions require a lightweight protected session/PIN
- Cloudflared public access defaults to read-only
- secrets must not be embedded in frontend JavaScript

## Command protocol boundary

The authenticated device socket carries raw telemetry plus separate versioned
`device-command.v1` and `device-ack.v1` envelopes. Commands are finite,
idempotent UUID-correlated requests; only a device `applied` acknowledgement
confirms a hardware state change. Expired, unsupported, or unsafe commands are
rejected without bypassing ESP32 safety.

## Phase 0 boundary

Phase 0 implements **contracts and repository foundation only**.

Phase 0 does not implement:

- FastAPI application logic
- React application logic
- ESP32 firmware logic
- Docker containers
- Nginx runtime configuration
- Cloudflared runtime configuration
- database migrations
- real sensor integration

Those are planned in later phases.
