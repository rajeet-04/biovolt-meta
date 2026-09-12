# Phase 0.2: Raw Device Telemetry Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define and test the exact versioned JSON payload that the ESP32 will later transmit to FastAPI every 500 ms.

**Architecture:** Raw telemetry contains only values that the ESP32 directly measures or owns: BPV voltage, ADC counts, BPW34 optical receiver measurements, temperature, lux, actuator state, control state, health state, sequence number, and uptime. Current, power, OD680, biomass, CO2 biofixation, cumulative energy, and wall-clock time are deliberately excluded because FastAPI owns those derived values.

**Tech Stack:** JSON Schema Draft 2020-12, JSON examples, Python 3.11+, `jsonschema`, `pytest`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Canonical payload field names use `snake_case`.
- The schema identifier is `device-telemetry.v1` and payloads carry `schema_version: 1`.
- `device_id` and `cell_id` are non-empty strings.
- `sequence` is an integer greater than or equal to 0 and increments once per telemetry frame.
- `uptime_ms` is an integer greater than or equal to 0.
- BPV voltage is transmitted in millivolts as `bpv_voltage_mv`.
- The ADC code used for BPV voltage is transmitted as `bpv_adc_raw` for diagnostics.
- BPW34 optical acquisition is transmitted as raw ADC count and converted voltage, not as OD680.
- Temperature and lux may be `null` when the physical sensor is unavailable.
- Every nullable sensor value has a corresponding health boolean.
- Current, power, OD680, biomass, CO2, energy, and server timestamp are forbidden in raw telemetry.
- `grow_led_pwm` is an integer from 0 through 255.
- `mode` is one of `monitor`, `passive`, `adaptive`, `manual`.
- `optimizer_direction` is one of `-1`, `0`, `1`; `0` means no active perturbation direction.

---

### Task 1: Write the raw telemetry tests first

**Files:**
- Create: `tests/contracts/test_device_telemetry_schema.py`

**Interfaces:**
- Consumes: `shared/schemas/device-telemetry.v1.schema.json` and `shared/examples/device-telemetry.example.json` once they exist.
- Produces: validation tests that later firmware and simulator payloads must satisfy.

- [ ] **Step 1: Create a schema loader and canonical-example test**

```python
import json
from copy import deepcopy
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "shared/schemas/device-telemetry.v1.schema.json"
EXAMPLE_PATH = ROOT / "shared/examples/device-telemetry.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(SCHEMA_PATH))


def valid_payload() -> dict:
    return load_json(EXAMPLE_PATH)


def test_canonical_device_telemetry_example_is_valid() -> None:
    errors = list(validator().iter_errors(valid_payload()))
    assert errors == []
```

- [ ] **Step 2: Add tests proving derived fields are forbidden**

```python
@pytest.mark.parametrize(
    "field",
    [
        "current_ua",
        "power_uw",
        "od680",
        "biomass_g_l",
        "co2_biofixed_g",
        "cumulative_energy_mj",
        "timestamp",
    ],
)
def test_raw_payload_rejects_backend_owned_derived_fields(field: str) -> None:
    payload = valid_payload()
    payload[field] = 1
    errors = list(validator().iter_errors(payload))
    assert errors
```

- [ ] **Step 3: Add null-and-health behavior tests**

```python
def test_temperature_may_be_null_when_health_is_false() -> None:
    payload = valid_payload()
    payload["environment"]["temperature_c"] = None
    payload["health"]["temperature_ok"] = False
    assert list(validator().iter_errors(payload)) == []


def test_lux_may_be_null_when_health_is_false() -> None:
    payload = valid_payload()
    payload["environment"]["lux"] = None
    payload["health"]["light_sensor_ok"] = False
    assert list(validator().iter_errors(payload)) == []
```

- [ ] **Step 4: Add boundary tests**

```python
@pytest.mark.parametrize("pwm", [-1, 256])
def test_grow_led_pwm_outside_byte_range_is_rejected(pwm: int) -> None:
    payload = valid_payload()
    payload["actuators"]["grow_led_pwm"] = pwm
    assert list(validator().iter_errors(payload))


def test_negative_sequence_is_rejected() -> None:
    payload = valid_payload()
    payload["sequence"] = -1
    assert list(validator().iter_errors(payload))


def test_negative_uptime_is_rejected() -> None:
    payload = valid_payload()
    payload["uptime_ms"] = -1
    assert list(validator().iter_errors(payload))
```

- [ ] **Step 5: Run the tests and confirm they fail because schema/example files do not yet exist**

```bash
python -m pytest tests/contracts/test_device_telemetry_schema.py -v
```

Expected: collection or test failure indicating that `device-telemetry.v1.schema.json` and/or the example file is missing.

---

### Task 2: Define the v1 raw telemetry schema

**Files:**
- Create: `shared/schemas/device-telemetry.v1.schema.json`

**Interfaces:**
- Consumes: conventions from `docs/protocols/data-contract.md`.
- Produces: canonical `DeviceTelemetryV1` contract used by ESP32, simulator, and FastAPI.

- [ ] **Step 1: Create the schema using Draft 2020-12**

Use this exact top-level shape:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://biovolt.local/schemas/device-telemetry.v1.schema.json",
  "title": "BioVolt Device Telemetry v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "device_id",
    "sequence",
    "uptime_ms",
    "cell_id",
    "electrical",
    "optical",
    "environment",
    "actuators",
    "control",
    "health"
  ],
  "properties": {
    "schema_version": {"const": 1},
    "device_id": {"type": "string", "minLength": 1, "maxLength": 64},
    "sequence": {"type": "integer", "minimum": 0},
    "uptime_ms": {"type": "integer", "minimum": 0},
    "cell_id": {"type": "string", "minLength": 1, "maxLength": 64},
    "electrical": {"$ref": "#/$defs/electrical"},
    "optical": {"$ref": "#/$defs/optical"},
    "environment": {"$ref": "#/$defs/environment"},
    "actuators": {"$ref": "#/$defs/actuators"},
    "control": {"$ref": "#/$defs/control"},
    "health": {"$ref": "#/$defs/health"}
  }
}
```

- [ ] **Step 2: Define the `electrical` object**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["bpv_voltage_mv", "bpv_adc_raw"],
  "properties": {
    "bpv_voltage_mv": {"type": ["number", "null"]},
    "bpv_adc_raw": {"type": ["integer", "null"], "minimum": -32768, "maximum": 32767}
  }
}
```

The voltage may be `null` when ADS1115 health is false. Do not impose an artificial positive-only constraint because signed diagnostic readings may occur during offset calibration or reversed wiring.

- [ ] **Step 3: Define the `optical` object**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["bpw34_raw", "bpw34_voltage_mv", "led_680_enabled"],
  "properties": {
    "bpw34_raw": {"type": ["integer", "null"], "minimum": -32768, "maximum": 32767},
    "bpw34_voltage_mv": {"type": ["number", "null"]},
    "led_680_enabled": {"type": "boolean"}
  }
}
```

Do not include `od680` in this object.

- [ ] **Step 4: Define the `environment` object**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["temperature_c", "lux"],
  "properties": {
    "temperature_c": {"type": ["number", "null"], "minimum": -55, "maximum": 125},
    "lux": {"type": ["number", "null"], "minimum": 0}
  }
}
```

- [ ] **Step 5: Define the `actuators` object**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["grow_led_pwm", "mixer_on"],
  "properties": {
    "grow_led_pwm": {"type": "integer", "minimum": 0, "maximum": 255},
    "mixer_on": {"type": "boolean"}
  }
}
```

- [ ] **Step 6: Define the `control` object**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["mode", "optimizer_direction"],
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["monitor", "passive", "adaptive", "manual"]
    },
    "optimizer_direction": {
      "type": "integer",
      "enum": [-1, 0, 1]
    }
  }
}
```

- [ ] **Step 7: Define the `health` object**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "ads1115_ok",
    "bpw34_ok",
    "temperature_ok",
    "light_sensor_ok"
  ],
  "properties": {
    "ads1115_ok": {"type": "boolean"},
    "bpw34_ok": {"type": "boolean"},
    "temperature_ok": {"type": "boolean"},
    "light_sensor_ok": {"type": "boolean"}
  }
}
```

- [ ] **Step 8: Ensure `$defs` contains the six objects above and all objects use `additionalProperties: false`**

This prevents accidental field drift such as an ESP32 developer silently adding `power_uw` to raw telemetry.

---

### Task 3: Add the canonical raw telemetry example

**Files:**
- Create: `shared/examples/device-telemetry.example.json`

**Interfaces:**
- Consumes: `device-telemetry.v1.schema.json`.
- Produces: a single known-good payload for firmware, simulator, backend, documentation, and tests.

- [ ] **Step 1: Create the canonical example**

```json
{
  "schema_version": 1,
  "device_id": "biovolt-01",
  "sequence": 1245,
  "uptime_ms": 582340,
  "cell_id": "cell-a",
  "electrical": {
    "bpv_voltage_mv": 438.2,
    "bpv_adc_raw": 18431
  },
  "optical": {
    "bpw34_raw": 17320,
    "bpw34_voltage_mv": 1321.4,
    "led_680_enabled": true
  },
  "environment": {
    "temperature_c": 26.4,
    "lux": 910.0
  },
  "actuators": {
    "grow_led_pwm": 130,
    "mixer_on": false
  },
  "control": {
    "mode": "adaptive",
    "optimizer_direction": 1
  },
  "health": {
    "ads1115_ok": true,
    "bpw34_ok": true,
    "temperature_ok": true,
    "light_sensor_ok": true
  }
}
```

- [ ] **Step 2: Confirm the example contains no backend-owned derived values**

Search:

```bash
grep -E 'current_ua|power_uw|od680|biomass|co2_biofixed|cumulative_energy|"timestamp"' shared/examples/device-telemetry.example.json
```

Expected: no output and a non-zero grep status.

---

### Task 4: Run tests and commit Module 0.2

**Files:**
- Test: `tests/contracts/test_device_telemetry_schema.py`
- Create: `shared/schemas/device-telemetry.v1.schema.json`
- Create: `shared/examples/device-telemetry.example.json`

**Interfaces:**
- Produces: stable raw device payload contract for Phase 1 simulator and later ESP32 firmware.

- [ ] **Step 1: Run the raw telemetry tests**

```bash
python -m pytest tests/contracts/test_device_telemetry_schema.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Validate that additional unexpected fields are rejected**

Add this test if not already covered:

```python
def test_unknown_top_level_field_is_rejected() -> None:
    payload = valid_payload()
    payload["mystery"] = 123
    assert list(validator().iter_errors(payload))
```

Run the test again and confirm it passes.

- [ ] **Step 3: Commit**

```bash
git add shared/schemas/device-telemetry.v1.schema.json shared/examples/device-telemetry.example.json tests/contracts/test_device_telemetry_schema.py
git commit -m "feat: define raw BioVolt telemetry contract"
```

## Module 0.2 Exit Criteria

- [ ] Raw payload schema is versioned and rejects extra fields.
- [ ] BPV voltage and ADC count are present.
- [ ] BPW34 raw and converted voltage are present.
- [ ] OD680 is absent.
- [ ] Current and power are absent.
- [ ] Biomass, carbon, energy, and wall-clock time are absent.
- [ ] Sequence and uptime are mandatory.
- [ ] Null sensor values are supported.
- [ ] Health flags are mandatory.
- [ ] Control mode and optimizer direction are bounded enums.
- [ ] Canonical example validates.
- [ ] Malformed payload tests fail validation as expected.
