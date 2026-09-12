# BioVolt Device Simulator

This package emulates an ESP32 device so backend and frontend development can
proceed without physical hardware. It emits deterministic telemetry using the
shared `device-telemetry.v1` contract.

The simulator is optional and disposable development infrastructure. It exists
to unblock backend and frontend work before an ESP32 is available; it is not a
production data source.

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

## Run modes

Run the normal deterministic simulator with the settings loaded from the
environment:

```bash
biovolt-simulator
```

To exercise a sensor-null fault, select one explicit fault mode. The generated
value is set to `null` and its health flag is set to `false`:

```bash
biovolt-simulator --fault temperature_null
```

To exercise backend rejection handling, remove the required `sequence` field
from every tenth frame. `--malformed-every 0` (the default) disables this mode;
malformed frames are intentionally not schema-valid:

```bash
biovolt-simulator --malformed-every 10
```

Command-line flags override their corresponding `BIOVOLT_SIM_` environment
values. The startup summary includes the target, cadence, seed, device, and
cell, but never prints the device token.

## Docker

Build the image from the repository root:

```bash
docker build -f simulator/Dockerfile -t biovolt-simulator:phase1 .
```

The container starts the `biovolt-simulator` command. Configure it entirely
through `BIOVOLT_SIM_` environment variables; the token is read for the
authenticated WebSocket connection and is never included in the startup
summary or logs:

```bash
docker run --rm \
  -e BIOVOLT_SIM_BACKEND_WS_URL=ws://host.docker.internal:8000/ws/device \
  -e BIOVOLT_SIM_DEVICE_ID=biovolt-sim-01 \
  -e BIOVOLT_SIM_CELL_ID=cell-a \
  -e BIOVOLT_SIM_DEVICE_TOKEN=replace-with-a-device-token \
  biovolt-simulator:phase1
```

## Switchover to ESP32

Stop the simulator while keeping the backend running:

```bash
docker compose stop simulator
docker compose up -d backend
```

Configure the ESP32 to connect to
`ws://<laptop-hotspot-ip>:8000/ws/device` with a unique device ID and the
configured shared token. It must send the same Phase 0
`device-telemetry.v1` JSON shape and authentication headers:

```text
X-BioVolt-Device-ID: <device_id>
Authorization: Bearer <shared-token>
```

No simulator install or container, backend feature flag, second database table,
or alternate endpoint is needed. FastAPI processing, persistence, and
dashboard fanout remain unchanged.
