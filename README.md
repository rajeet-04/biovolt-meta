# BioVolt

BioVolt is an adaptive living biophotovoltaic research prototype for MetaMorph 2.0.

## Architecture

- ESP32: sensing, local safety, actuation, Perturb & Observe control
- FastAPI: scientific derivations, experiments, persistence, WebSockets
- React PWA: visualization and operator interaction

## Repository Areas

- `firmware/esp32/`
- `backend/`
- `frontend/`
- `simulator/`
- `shared/`
- `docs/`
- `scripts/`
- `tests/`

## Current Development Phase

Phase 0: repository foundation and versioned protocol contracts.

## Scientific Ownership Rule

Raw ESP32 telemetry contains measured/control-state values only. Current, power, OD680, biomass, estimated CO2 biofixed into biomass, cumulative energy, and server timestamps are derived by the backend.
