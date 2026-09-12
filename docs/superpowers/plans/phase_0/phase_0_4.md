# Phase 0.4: Command, Calibration, Experiment, and Event Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define versioned contracts for commands sent to the ESP32, calibration profiles used by FastAPI, experiment definitions, and system events emitted during runtime.

**Architecture:** Control and experiment concepts are separated from telemetry. Commands are explicit, typed requests; calibration profiles carry scientific constants; experiments carry reproducible run configuration; system events carry discrete state changes and optimizer/safety events. Each contract has one canonical example and dedicated validation tests.

**Tech Stack:** JSON Schema Draft 2020-12, JSON examples, Python 3.11+, `jsonschema`, `pytest`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Every payload uses `schema_version: 1`.
- Command IDs, profile IDs, experiment IDs, device IDs, and cell IDs are non-empty strings.
- Commands never embed secrets.
- Manual commands remain subject to ESP32 safety rules in later phases.
- Calibration profiles are immutable references for completed experiments. A later change creates a new profile ID rather than mutating historical meaning.
- Phase 0 supports only a linear OD-to-biomass model.
- Reactor volume is stored in litres.
- Experiment modes are exactly `monitor`, `passive`, `adaptive`, `manual`.
- System events are discrete records and are not mixed into the 500 ms telemetry stream.

---

### Task 1: Write contract tests first

**Files:**
- Create: `tests/contracts/test_control_contracts.py`

**Interfaces:**
- Consumes: four schemas and four canonical examples once created.
- Produces: one validation gate for commands, calibration, experiments, and events.

- [ ] **Step 1: Add reusable validator helpers**

```python
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def assert_valid(schema_path: str, example_path: str) -> None:
    schema = load_json(schema_path)
    example = load_json(example_path)
    errors = list(Draft202012Validator(schema).iter_errors(example))
    assert errors == []
```

- [ ] **Step 2: Add canonical-example tests**

```python
def test_device_command_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/device-command.v1.schema.json",
        "shared/examples/device-command.example.json",
    )


def test_calibration_profile_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/calibration-profile.v1.schema.json",
        "shared/examples/calibration-profile.example.json",
    )


def test_experiment_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/experiment.v1.schema.json",
        "shared/examples/experiment.example.json",
    )


def test_system_event_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/system-event.v1.schema.json",
        "shared/examples/system-event.example.json",
    )
```

- [ ] **Step 3: Add command boundary tests**

```python
@pytest.mark.parametrize("invalid_pwm", [-1, 256])
def test_set_led_pwm_rejects_values_outside_byte_range(invalid_pwm: int) -> None:
    schema = load_json("shared/schemas/device-command.v1.schema.json")
    payload = {
        "schema_version": 1,
        "command_id": "cmd-test",
        "type": "set_led_pwm",
        "payload": {"value": invalid_pwm},
    }
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_unknown_command_type_is_rejected() -> None:
    schema = load_json("shared/schemas/device-command.v1.schema.json")
    payload = {
        "schema_version": 1,
        "command_id": "cmd-test",
        "type": "do_magic",
        "payload": {},
    }
    assert list(Draft202012Validator(schema).iter_errors(payload))
```

- [ ] **Step 4: Add calibration boundary tests**

```python
def test_calibration_rejects_nonpositive_load_resistance() -> None:
    schema = load_json("shared/schemas/calibration-profile.v1.schema.json")
    payload = load_json("shared/examples/calibration-profile.example.json")
    payload["electrical"]["load_resistance_ohm"] = 0
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_calibration_rejects_nonpositive_reactor_volume() -> None:
    schema = load_json("shared/schemas/calibration-profile.v1.schema.json")
    payload = load_json("shared/examples/calibration-profile.example.json")
    payload["reactor"]["volume_l"] = 0
    assert list(Draft202012Validator(schema).iter_errors(payload))
```

- [ ] **Step 5: Add experiment mode tests**

```python
def test_unknown_experiment_mode_is_rejected() -> None:
    schema = load_json("shared/schemas/experiment.v1.schema.json")
    payload = load_json("shared/examples/experiment.example.json")
    payload["mode"] = "turbo"
    assert list(Draft202012Validator(schema).iter_errors(payload))
```

- [ ] **Step 6: Run the test module and confirm it fails because schemas/examples are not present**

```bash
python -m pytest tests/contracts/test_control_contracts.py -v
```

Expected: failure on missing contract files.

---

### Task 2: Define the device command contract

**Files:**
- Create: `shared/schemas/device-command.v1.schema.json`
- Create: `shared/examples/device-command.example.json`

**Interfaces:**
- Consumes: experiment mode enum and actuator boundaries from prior modules.
- Produces: the future FastAPI-to-ESP32 command protocol.

- [ ] **Step 1: Define supported command types**

The v1 command schema supports exactly:

```text
set_mode
set_led_pwm
set_mixer
set_mixer_schedule
start_experiment
stop_experiment
sync_config
ping
```

- [ ] **Step 2: Define the common envelope**

```json
{
  "schema_version": 1,
  "command_id": "cmd-01783",
  "type": "set_led_pwm",
  "payload": {
    "value": 130
  }
}
```

The schema must use `oneOf` so each `type` requires its matching payload shape.

- [ ] **Step 3: Define payload shapes**

`set_mode`:

```json
{"mode": "adaptive"}
```

Mode enum: `monitor`, `passive`, `adaptive`, `manual`.

`set_led_pwm`:

```json
{"value": 130}
```

Allowed range: 0 to 255.

`set_mixer`:

```json
{"on": true}
```

`set_mixer_schedule`:

```json
{"interval_s": 300, "duration_s": 5}
```

Both are non-negative integers and `duration_s` must be at least 1 when the schedule is used.

`start_experiment`:

```json
{"experiment_id": "EXP-2026-001"}
```

`stop_experiment`:

```json
{"experiment_id": "EXP-2026-001"}
```

`sync_config`:

```json
{
  "calibration_profile_id": "cal-001",
  "load_resistance_ohm": 100000,
  "led_pwm_min": 20,
  "led_pwm_max": 220,
  "mixer_max_runtime_s": 10,
  "mixer_cooldown_s": 60
}
```

`ping`:

```json
{}
```

- [ ] **Step 4: Use `additionalProperties: false` in the envelope and every payload variant**

This prevents commands from silently acquiring undefined behavior.

- [ ] **Step 5: Create the canonical command example as `set_led_pwm`**

```json
{
  "schema_version": 1,
  "command_id": "cmd-01783",
  "type": "set_led_pwm",
  "payload": {
    "value": 130
  }
}
```

---

### Task 3: Define the calibration profile contract

**Files:**
- Create: `shared/schemas/calibration-profile.v1.schema.json`
- Create: `shared/examples/calibration-profile.example.json`

**Interfaces:**
- Consumes: scientific ownership/formulas from Module 0.3.
- Produces: reproducible constants required for electrical and optical derivations.

- [ ] **Step 1: Define the required calibration structure**

```json
{
  "schema_version": 1,
  "profile_id": "cal-001",
  "cell_id": "cell-a",
  "electrical": {
    "load_resistance_ohm": 100000,
    "ads1115_offset_mv": -0.42
  },
  "optical": {
    "bpw34_dark_raw": 320,
    "bpw34_blank_raw": 23840
  },
  "biomass": {
    "model": "linear",
    "slope": 0.501,
    "intercept": 0.012
  },
  "reactor": {
    "volume_l": 0.25
  }
}
```

- [ ] **Step 2: Add schema constraints**

- `load_resistance_ohm`: number, exclusive minimum 0
- `ads1115_offset_mv`: number
- `bpw34_dark_raw`: integer
- `bpw34_blank_raw`: integer
- `model`: constant string `linear`
- `slope`: number, exclusive minimum 0
- `intercept`: number
- `volume_l`: number, exclusive minimum 0
- all nested objects: `additionalProperties: false`

- [ ] **Step 3: Document that calibration examples are not universal biological constants**

Add a short note to `docs/protocols/data-contract.md` explaining that the example values are structural examples and must not be copied into experiments without calibration.

---

### Task 4: Define the experiment contract

**Files:**
- Create: `shared/schemas/experiment.v1.schema.json`
- Create: `shared/examples/experiment.example.json`

**Interfaces:**
- Consumes: mode enum and calibration profile identity.
- Produces: reproducible experiment configuration used by Phase 1+ experiment lifecycle APIs.

- [ ] **Step 1: Define the experiment envelope**

```json
{
  "schema_version": 1,
  "experiment_id": "EXP-2026-001",
  "name": "Passive baseline",
  "cell_id": "cell-a",
  "mode": "passive",
  "calibration_profile_id": "cal-001",
  "configuration": {
    "grow_led_pwm": 120,
    "mixer_interval_s": 300,
    "mixer_duration_s": 5
  },
  "notes": "Baseline run before adaptive control."
}
```

- [ ] **Step 2: Constrain fields**

- `experiment_id`: non-empty string, max 64
- `name`: non-empty string, max 120
- `cell_id`: non-empty string, max 64
- `mode`: `monitor`, `passive`, `adaptive`, `manual`
- `calibration_profile_id`: non-empty string, max 64
- `grow_led_pwm`: integer 0 through 255 or `null`
- `mixer_interval_s`: integer >= 0 or `null`
- `mixer_duration_s`: integer >= 0 or `null`
- `notes`: string, max 1000

- [ ] **Step 3: Keep runtime timestamps out of the experiment-definition schema**

`started_at`, `ended_at`, and runtime status belong to backend persistence models in Phase 1, not the immutable experiment-definition contract.

---

### Task 5: Define the system event contract

**Files:**
- Create: `shared/schemas/system-event.v1.schema.json`
- Create: `shared/examples/system-event.example.json`

**Interfaces:**
- Consumes: device/cell IDs and event vocabulary.
- Produces: discrete event record used later for logs and dashboard timelines.

- [ ] **Step 1: Define the event envelope**

```json
{
  "schema_version": 1,
  "event_id": "evt-00042",
  "timestamp": "2026-08-23T17:42:01+05:30",
  "device_id": "biovolt-01",
  "cell_id": "cell-a",
  "type": "optimizer_step",
  "data": {
    "previous_pwm": 120,
    "new_pwm": 128,
    "previous_power_uw": 1.71,
    "current_power_uw": 1.83,
    "decision": "continue"
  }
}
```

- [ ] **Step 2: Define the v1 event type vocabulary**

```text
device_connected
device_disconnected
sensor_fault
sensor_recovered
experiment_started
experiment_stopped
optimizer_step
safety_override
mixer_activated
calibration_changed
```

- [ ] **Step 3: Define event data as an object while keeping the event type itself strict**

For Phase 0, `data` may be an arbitrary JSON object because different event types have materially different fields. `type` remains a strict enum. More specific per-event data schemas may be introduced only when Phase 1+ requirements justify them.

---

### Task 6: Run contract tests and commit Module 0.4

**Files:**
- Test: `tests/contracts/test_control_contracts.py`
- Create: four schemas
- Create: four examples
- Modify: `docs/protocols/data-contract.md`

**Interfaces:**
- Produces: stable control, calibration, experiment, and event contracts.

- [ ] **Step 1: Run tests**

```bash
python -m pytest tests/contracts/test_control_contracts.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Add a test proving experiment runtime timestamps are not accepted**

```python
def test_experiment_definition_rejects_runtime_timestamp_fields() -> None:
    schema = load_json("shared/schemas/experiment.v1.schema.json")
    payload = load_json("shared/examples/experiment.example.json")
    payload["started_at"] = "2026-08-23T17:00:00+05:30"
    assert list(Draft202012Validator(schema).iter_errors(payload))
```

Run the module again and confirm it passes.

- [ ] **Step 3: Commit**

```bash
git add shared/schemas/device-command.v1.schema.json shared/schemas/calibration-profile.v1.schema.json shared/schemas/experiment.v1.schema.json shared/schemas/system-event.v1.schema.json shared/examples/device-command.example.json shared/examples/calibration-profile.example.json shared/examples/experiment.example.json shared/examples/system-event.example.json tests/contracts/test_control_contracts.py docs/protocols/data-contract.md
git commit -m "feat: define control and experiment contracts"
```

## Module 0.4 Exit Criteria

- [ ] Device commands are typed and bounded.
- [ ] Unsupported command types are rejected.
- [ ] Calibration profiles contain load resistance, optical references, biomass regression coefficients, and reactor volume.
- [ ] Calibration examples are explicitly non-universal.
- [ ] Experiment definitions are reproducible and reference calibration profiles.
- [ ] Experiment runtime timestamps remain out of the definition contract.
- [ ] System event types are versioned and strict.
- [ ] Canonical examples validate.
- [ ] Boundary and malformed-payload tests pass.
