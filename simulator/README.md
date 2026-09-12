# BioVolt Device Simulator

This package emulates an ESP32 device so backend and frontend development can
proceed without physical hardware. It emits deterministic telemetry using the
shared `device-telemetry.v1` contract.

## Development setup

```bash
cd simulator
python -m pip install -e '.[dev]'
pytest -v
```

Simulator settings are loaded from `BIOVOLT_SIM_` environment variables. The
WebSocket URL and device token are required; the default cadence is 500 ms.

```bash
export BIOVOLT_SIM_BACKEND_WS_URL=ws://localhost:8000/ws/device
export BIOVOLT_SIM_DEVICE_TOKEN=replace-with-a-device-token
```

The remaining defaults are `biovolt-sim-01` for the device ID, `cell-a` for the
cell ID, seed `42`, and initial sequence `1`.
