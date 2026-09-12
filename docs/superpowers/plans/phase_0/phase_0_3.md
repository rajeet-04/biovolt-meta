# Phase 0.3: Processed Scientific Telemetry Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define and test the exact backend-owned scientific telemetry payload that FastAPI will later broadcast to the PWA and persist for experiments.

**Architecture:** FastAPI transforms raw device telemetry plus a selected calibration profile into processed telemetry. This layer owns scientific derivations so firmware and frontend do not duplicate formulas. The processed payload preserves device identity and actuator/control context while adding wall-clock time, current, power, cumulative energy, OD680, biomass, and estimated CO2 biofixed into biomass.

**Tech Stack:** JSON Schema Draft 2020-12, Markdown scientific derivation notes, Python 3.11+, `jsonschema`, `pytest`.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- `timestamp` is ISO 8601 with timezone and is supplied by FastAPI, not ESP32.
- Electrical current is backend-derived from calibrated load resistance and measured BPV voltage.
- `current_ua = (voltage_mv / 1000) / load_resistance_ohm * 1_000_000`.
- `power_uw = (voltage_mv / 1000)^2 / load_resistance_ohm * 1_000_000`.
- Cumulative energy is integrated by the backend and represented in millijoules.
- OD680 is backend-derived from BPW34 measurements and calibration references.
- OD680 formula: `-log10((I_sample - I_dark) / (I_blank - I_dark))`.
- Biomass conversion requires a selected calibration profile.
- Phase 0 defines a linear biomass calibration model only: `biomass_g_l = slope * od680 + intercept`.
- `biomass_total_g = biomass_g_l * reactor_volume_l`.
- `biomass_delta_g` is relative to the experiment baseline, not the absolute biomass total.
- `co2_biofixed_g = max(biomass_delta_g, 0) * 1.83` for the initial model.
- The product copy is `estimated CO2 biofixed into biomass`.
- Processed telemetry may contain `null` derived values when required raw inputs or calibration data are unavailable.

---

### Task 1: Write processed telemetry schema tests first

**Files:**
- Create: `tests/contracts/test_processed_telemetry_schema.py`

**Interfaces:**
- Consumes: `shared/schemas/processed-telemetry.v1.schema.json` and canonical example.
- Produces: tests protecting scientific field names, units, enums, and required context.

- [ ] **Step 1: Create loader and valid-example test**

```python
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "shared/schemas/processed-telemetry.v1.schema.json"
EXAMPLE_PATH = ROOT / "shared/examples/processed-telemetry.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(SCHEMA_PATH))


def payload() -> dict:
    return load_json(EXAMPLE_PATH)


def test_canonical_processed_telemetry_example_is_valid() -> None:
    assert list(validator().iter_errors(payload())) == []
```

- [ ] **Step 2: Add tests requiring scientific fields to live in their named groups**

```python
def test_processed_electrical_group_contains_current_power_and_energy() -> None:
    electrical = payload()["electrical"]
    assert "current_ua" in electrical
    assert "power_uw" in electrical
    assert "cumulative_energy_mj" in electrical


def test_processed_biological_group_contains_od_biomass_and_carbon() -> None:
    biological = payload()["biological"]
    assert "od680" in biological
    assert "biomass_g_l" in biological
    assert "biomass_total_g" in biological
    assert "biomass_delta_g" in biological
    assert "co2_biofixed_g" in biological
```

- [ ] **Step 3: Add tests for time and unit boundaries**

```python
def test_processed_payload_requires_server_timestamp() -> None:
    data = payload()
    del data["timestamp"]
    assert list(validator().iter_errors(data))


def test_negative_load_resistance_is_rejected() -> None:
    data = payload()
    data["electrical"]["load_resistance_ohm"] = -100
    assert list(validator().iter_errors(data))


def test_negative_cumulative_energy_is_rejected() -> None:
    data = payload()
    data["electrical"]["cumulative_energy_mj"] = -0.1
    assert list(validator().iter_errors(data))
```

- [ ] **Step 4: Add tests allowing unavailable derived values to be null**

```python
@pytest.mark.parametrize(
    "group,field",
    [
        ("electrical", "current_ua"),
        ("electrical", "power_uw"),
        ("biological", "od680"),
        ("biological", "biomass_g_l"),
        ("biological", "co2_biofixed_g"),
    ],
)
def test_derived_values_may_be_null_when_inputs_are_unavailable(group: str, field: str) -> None:
    data = payload()
    data[group][field] = None
    assert list(validator().iter_errors(data)) == []
```

- [ ] **Step 5: Run tests and verify they fail before schema/example creation**

```bash
python -m pytest tests/contracts/test_processed_telemetry_schema.py -v
```

Expected: failure because schema/example files are not present.

---

### Task 2: Define the processed telemetry v1 schema

**Files:**
- Create: `shared/schemas/processed-telemetry.v1.schema.json`

**Interfaces:**
- Consumes: device identity/mode naming from Module 0.2 and units from Module 0.1.
- Produces: backend-to-PWA and backend-to-persistence payload contract.

- [ ] **Step 1: Define the top-level processed payload**

Use this exact required shape:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://biovolt.local/schemas/processed-telemetry.v1.schema.json",
  "title": "BioVolt Processed Telemetry v1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "device_id",
    "cell_id",
    "sequence",
    "timestamp",
    "electrical",
    "biological",
    "environment",
    "actuators",
    "control"
  ],
  "properties": {
    "schema_version": {"const": 1},
    "device_id": {"type": "string", "minLength": 1, "maxLength": 64},
    "cell_id": {"type": "string", "minLength": 1, "maxLength": 64},
    "sequence": {"type": "integer", "minimum": 0},
    "timestamp": {"type": "string", "format": "date-time"},
    "electrical": {"$ref": "#/$defs/electrical"},
    "biological": {"$ref": "#/$defs/biological"},
    "environment": {"$ref": "#/$defs/environment"},
    "actuators": {"$ref": "#/$defs/actuators"},
    "control": {"$ref": "#/$defs/control"}
  }
}
```

- [ ] **Step 2: Define `electrical`**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "voltage_mv",
    "current_ua",
    "power_uw",
    "load_resistance_ohm",
    "cumulative_energy_mj"
  ],
  "properties": {
    "voltage_mv": {"type": ["number", "null"]},
    "current_ua": {"type": ["number", "null"]},
    "power_uw": {"type": ["number", "null"]},
    "load_resistance_ohm": {"type": "number", "exclusiveMinimum": 0},
    "cumulative_energy_mj": {"type": ["number", "null"], "minimum": 0}
  }
}
```

- [ ] **Step 3: Define `biological`**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "od680",
    "biomass_g_l",
    "biomass_total_g",
    "biomass_delta_g",
    "co2_biofixed_g"
  ],
  "properties": {
    "od680": {"type": ["number", "null"], "minimum": 0},
    "biomass_g_l": {"type": ["number", "null"], "minimum": 0},
    "biomass_total_g": {"type": ["number", "null"], "minimum": 0},
    "biomass_delta_g": {"type": ["number", "null"]},
    "co2_biofixed_g": {"type": ["number", "null"], "minimum": 0}
  }
}
```

`biomass_delta_g` may temporarily be negative because biological estimates can fluctuate with sensor noise. Carbon biofixation remains non-negative in v1.

- [ ] **Step 4: Define `environment`**

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["temperature_c", "lux"],
  "properties": {
    "temperature_c": {"type": ["number", "null"]},
    "lux": {"type": ["number", "null"], "minimum": 0}
  }
}
```

- [ ] **Step 5: Reuse actuator and control field names from raw telemetry**

`actuators`:

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

`control`:

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": ["mode"],
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["monitor", "passive", "adaptive", "manual"]
    }
  }
}
```

---

### Task 3: Add the canonical processed telemetry example

**Files:**
- Create: `shared/examples/processed-telemetry.example.json`

**Interfaces:**
- Consumes: processed schema.
- Produces: canonical PWA/backend example used in Phase 1 and Phase 2.

- [ ] **Step 1: Create this example**

```json
{
  "schema_version": 1,
  "device_id": "biovolt-01",
  "cell_id": "cell-a",
  "sequence": 1245,
  "timestamp": "2026-08-23T17:30:15.124+05:30",
  "electrical": {
    "voltage_mv": 438.2,
    "current_ua": 4.382,
    "power_uw": 1.920,
    "load_resistance_ohm": 100000,
    "cumulative_energy_mj": 8.431
  },
  "biological": {
    "od680": 0.823,
    "biomass_g_l": 0.424,
    "biomass_total_g": 0.106,
    "biomass_delta_g": 0.022,
    "co2_biofixed_g": 0.0403
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
    "mode": "adaptive"
  }
}
```

The numeric values are protocol examples only. They are not project performance claims.

---

### Task 4: Document scientific derivations and edge conditions

**Files:**
- Modify: `docs/protocols/data-contract.md`

**Interfaces:**
- Consumes: approved formulas.
- Produces: implementation-independent scientific meaning for later FastAPI code and tests.

- [ ] **Step 1: Add the electrical derivation section**

```markdown
## Electrical Derivations

Given `voltage_mv` and calibrated `load_resistance_ohm`:

`voltage_v = voltage_mv / 1000`

`current_ua = (voltage_v / load_resistance_ohm) * 1_000_000`

`power_uw = (voltage_v * voltage_v / load_resistance_ohm) * 1_000_000`

The load resistance is calibration/configuration data. It is not repeatedly transmitted by the ESP32.
```

- [ ] **Step 2: Add the OD680 derivation section**

```markdown
## OD680 Derivation

Inputs:
- `I_sample`: corrected BPW34 sample reading with 680 nm LED active
- `I_dark`: BPW34 dark reference
- `I_blank`: BPW34 blank-medium reference

`ratio = (I_sample - I_dark) / (I_blank - I_dark)`

`od680 = -log10(ratio)`

OD680 must be `null` when:
- a required optical input is missing,
- `I_blank <= I_dark`,
- `I_sample <= I_dark`, or
- the ratio is not physically valid for the v1 calculation.
```

- [ ] **Step 3: Add the biomass and carbon section**

```markdown
## Biomass and Carbon Estimate

Phase 0 defines a linear calibration model:

`biomass_g_l = slope * od680 + intercept`

`biomass_total_g = biomass_g_l * reactor_volume_l`

`biomass_delta_g = biomass_total_g - experiment_baseline_biomass_g`

`co2_biofixed_g = max(biomass_delta_g, 0) * 1.83`

This value is an estimated amount of CO2 biofixed into biomass. It is not direct gas-phase CO2 measurement and not a permanent sequestration claim.
```

---

### Task 5: Run tests and commit Module 0.3

**Files:**
- Test: `tests/contracts/test_processed_telemetry_schema.py`
- Create: `shared/schemas/processed-telemetry.v1.schema.json`
- Create: `shared/examples/processed-telemetry.example.json`
- Modify: `docs/protocols/data-contract.md`

**Interfaces:**
- Produces: stable backend-to-PWA scientific telemetry contract.

- [ ] **Step 1: Run processed telemetry tests**

```bash
python -m pytest tests/contracts/test_processed_telemetry_schema.py -v
```

Expected: all tests pass.

- [ ] **Step 2: Confirm raw and processed responsibilities remain separated**

Run:

```bash
grep -E 'current_ua|power_uw|od680|biomass_g_l|co2_biofixed_g|cumulative_energy_mj' shared/examples/device-telemetry.example.json && exit 1 || true
```

Expected: command succeeds because none of those fields occur in raw telemetry.

- [ ] **Step 3: Commit**

```bash
git add shared/schemas/processed-telemetry.v1.schema.json shared/examples/processed-telemetry.example.json tests/contracts/test_processed_telemetry_schema.py docs/protocols/data-contract.md
git commit -m "feat: define processed scientific telemetry contract"
```

## Module 0.3 Exit Criteria

- [ ] Processed payload includes wall-clock timestamp.
- [ ] Current is explicitly backend-derived.
- [ ] Power is explicitly backend-derived.
- [ ] Load resistance is positive and explicit in processed context.
- [ ] OD680 is explicitly backend-derived.
- [ ] Biomass conversion requires calibration.
- [ ] Carbon is described as estimated CO2 biofixed into biomass.
- [ ] Cumulative energy is represented in millijoules.
- [ ] Processed payload can carry null derived values when prerequisites are unavailable.
- [ ] Raw and processed schemas do not blur ownership.
- [ ] Canonical example validates and is clearly marked as non-performance data.
