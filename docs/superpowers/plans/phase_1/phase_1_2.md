# Phase 1.2: Contract Adapters and Scientific Calculation Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind the Phase 0 JSON contracts to typed backend models and implement pure, unit-tested scientific calculations for current, power, OD680, and processed telemetry construction.

**Architecture:** JSON Schema remains the protocol authority at the wire boundary. Pydantic models provide typed Python access after schema validation. Scientific calculations are pure functions under `domain/` so they are independently testable and reusable by WebSocket and persistence code.

**Tech Stack:** Python 3.11+, jsonschema, Pydantic v2, pytest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Do not modify Phase 0 schemas to make backend implementation easier.
- Canonical examples must pass both JSON Schema validation and Pydantic parsing.
- Pydantic serialization of processed telemetry must validate against the Phase 0 processed schema.
- Invalid/missing optical references yield `None`; no fabricated OD value.
- Current and power use the configured precision resistor and preserve Phase 0 units.
- Biomass and carbon remain `None` in this module unless explicit calibration coefficients are passed to a pure function.

---

### Task 1: Add JSON Schema contract loader

**Files:**
- Create: `backend/src/biovolt_backend/contracts/__init__.py`
- Create: `backend/src/biovolt_backend/contracts/loader.py`
- Create: `backend/tests/contracts/test_loader.py`

**Interfaces:**
- Produces `load_schema(filename: str) -> dict[str, object]`.
- Produces `validate_payload(filename: str, payload: dict[str, object]) -> None`.
- Repository root is resolved from the backend source path, not current working directory assumptions.

- [ ] **Step 1: Write failing canonical-example validation test**

```python
import json
from pathlib import Path

from biovolt_backend.contracts.loader import validate_payload


def test_canonical_device_example_validates():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    validate_payload("device-telemetry.v1.schema.json", payload)
```

- [ ] **Step 2: Run and verify failure**

```bash
pytest tests/contracts/test_loader.py -v
```

Expected: FAIL because loader does not exist.

- [ ] **Step 3: Implement loader**

```python
import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator


def repository_root() -> Path:
    return Path(__file__).resolve().parents[4]


@lru_cache(maxsize=None)
def load_schema(filename: str) -> dict[str, object]:
    path = repository_root() / "shared" / "schemas" / filename
    return json.loads(path.read_text(encoding="utf-8"))


def validate_payload(filename: str, payload: dict[str, object]) -> None:
    Draft202012Validator(load_schema(filename)).validate(payload)
```

- [ ] **Step 4: Add malformed-payload rejection test**

```python
import pytest
from jsonschema import ValidationError


def test_device_payload_without_sequence_is_rejected():
    payload = {
        "schema_version": 1,
        "device_id": "biovolt-01",
    }
    with pytest.raises(ValidationError):
        validate_payload("device-telemetry.v1.schema.json", payload)
```

- [ ] **Step 5: Run tests and commit**

```bash
pytest tests/contracts/test_loader.py -v
git add backend/src/biovolt_backend/contracts backend/tests/contracts/test_loader.py
git commit -m "feat: add Phase 0 contract loader"
```

---

### Task 2: Add typed raw and processed telemetry models

**Files:**
- Create: `backend/src/biovolt_backend/contracts/models.py`
- Create: `backend/tests/contracts/test_models.py`

**Interfaces:**
- Produces `DeviceTelemetryV1` matching Phase 0 raw schema.
- Produces `ProcessedTelemetryV1` matching Phase 0 processed schema.
- Nested model names are implementation details but fields must serialize to exact Phase 0 snake_case names.

- [ ] **Step 1: Write failing raw-model canonical test**

```python
import json
from pathlib import Path

from biovolt_backend.contracts.models import DeviceTelemetryV1


def test_raw_model_parses_canonical_example():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    model = DeviceTelemetryV1.model_validate(payload)
    assert model.schema_version == 1
    assert model.device_id
    assert model.cell_id
```

- [ ] **Step 2: Implement models by transcribing Phase 0 fields exactly**

Use strict range constraints where Phase 0 already defines them. Example shape:

```python
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class ElectricalRaw(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bpv_voltage_mv: float | None
    adc_raw: int | None


class OpticalRaw(BaseModel):
    model_config = ConfigDict(extra="forbid")
    bpw34_raw: float | None
    bpw34_voltage_mv: float | None
    led_680_enabled: bool


class EnvironmentRaw(BaseModel):
    model_config = ConfigDict(extra="forbid")
    temperature_c: float | None
    lux: float | None


class ActuatorState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grow_led_pwm: int = Field(ge=0, le=255)
    mixer_on: bool


class ControlState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["monitor", "passive", "adaptive", "manual"]
    optimizer_direction: int | None = None
```

Continue until the model exactly matches the merged Phase 0 contract.

- [ ] **Step 3: Add processed-model roundtrip test**

Construct a `ProcessedTelemetryV1`, call `model_dump(mode="json")`, then validate against `processed-telemetry.v1.schema.json` with `validate_payload`.

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/contracts -v
git add backend/src/biovolt_backend/contracts/models.py backend/tests/contracts/test_models.py
git commit -m "feat: add typed telemetry contract models"
```

---

### Task 3: Implement electrical calculations

**Files:**
- Create: `backend/src/biovolt_backend/domain/__init__.py`
- Create: `backend/src/biovolt_backend/domain/electrical.py`
- Create: `backend/tests/domain/test_electrical.py`

**Interfaces:**
- Produces `current_ua(voltage_mv: float, resistance_ohm: float) -> float`.
- Produces `power_uw(voltage_mv: float, resistance_ohm: float) -> float`.

- [ ] **Step 1: Write failing tests with known values**

```python
import pytest
from biovolt_backend.domain.electrical import current_ua, power_uw


def test_current_conversion_uses_mv_and_ohms():
    assert current_ua(438.2, 100_000.0) == pytest.approx(4.382)


def test_power_conversion_returns_microwatts():
    assert power_uw(438.2, 100_000.0) == pytest.approx(1.9201924)


def test_non_positive_resistance_is_rejected():
    with pytest.raises(ValueError):
        current_ua(438.2, 0)
```

- [ ] **Step 2: Implement minimal functions**

```python
def _validate_resistance(resistance_ohm: float) -> None:
    if resistance_ohm <= 0:
        raise ValueError("resistance_ohm must be > 0")


def current_ua(voltage_mv: float, resistance_ohm: float) -> float:
    _validate_resistance(resistance_ohm)
    return voltage_mv * 1000.0 / resistance_ohm


def power_uw(voltage_mv: float, resistance_ohm: float) -> float:
    _validate_resistance(resistance_ohm)
    return voltage_mv**2 / resistance_ohm
```

- [ ] **Step 3: Run tests and commit**

```bash
pytest tests/domain/test_electrical.py -v
git add backend/src/biovolt_backend/domain/electrical.py backend/tests/domain/test_electrical.py
git commit -m "feat: add BPV electrical calculations"
```

---

### Task 4: Implement OD680 calculation

**Files:**
- Create: `backend/src/biovolt_backend/domain/optical.py`
- Create: `backend/tests/domain/test_optical.py`

**Interfaces:**
- Produces `calculate_od680(sample_raw: float | None, dark_raw: float | None, blank_raw: float | None) -> float | None`.

- [ ] **Step 1: Write failing valid-case test**

```python
import math
import pytest
from biovolt_backend.domain.optical import calculate_od680


def test_od680_uses_dark_and_blank_correction():
    value = calculate_od680(sample_raw=12080, dark_raw=320, blank_raw=23840)
    expected = -math.log10((12080 - 320) / (23840 - 320))
    assert value == pytest.approx(expected)
```

- [ ] **Step 2: Write invalid-input tests**

```python
@pytest.mark.parametrize(
    "sample,dark,blank",
    [
        (None, 320, 23840),
        (12080, None, 23840),
        (12080, 320, None),
        (320, 320, 23840),
        (12080, 320, 320),
    ],
)
def test_invalid_optical_reference_returns_none(sample, dark, blank):
    assert calculate_od680(sample, dark, blank) is None
```

- [ ] **Step 3: Implement calculation without clamping**

```python
import math


def calculate_od680(
    sample_raw: float | None,
    dark_raw: float | None,
    blank_raw: float | None,
) -> float | None:
    if sample_raw is None or dark_raw is None or blank_raw is None:
        return None
    numerator = sample_raw - dark_raw
    denominator = blank_raw - dark_raw
    if numerator <= 0 or denominator <= 0:
        return None
    return -math.log10(numerator / denominator)
```

- [ ] **Step 4: Run tests and commit**

```bash
pytest tests/domain/test_optical.py -v
git add backend/src/biovolt_backend/domain/optical.py backend/tests/domain/test_optical.py
git commit -m "feat: add OD680 calculation"
```

---

### Task 5: Build processed telemetry from one raw frame

**Files:**
- Create: `backend/src/biovolt_backend/domain/processing.py`
- Create: `backend/tests/domain/test_processing.py`

**Interfaces:**
- Produces `ProcessingConfig(load_resistance_ohm, bpw34_dark_raw, bpw34_blank_raw)`.
- Produces `build_processed_telemetry(raw: DeviceTelemetryV1, timestamp: datetime, config: ProcessingConfig, cumulative_energy_mj: float) -> ProcessedTelemetryV1`.

- [ ] **Step 1: Write failing processing test**

Use canonical raw telemetry, a fixed UTC timestamp, `100_000 Ω`, and known optical references. Assert processed voltage equals raw voltage, current/power match the pure functions, and OD equals `calculate_od680`.

- [ ] **Step 2: Implement `ProcessingConfig` and builder**

Rules:
- if raw BPV voltage is `None`, current and power are `None`.
- if optical sample/reference inputs are invalid, OD680 is `None`.
- biomass/carbon fields remain `None` in Phase 1.
- timestamp is supplied by caller and serialized as timezone-aware ISO 8601.
- cumulative energy is supplied by caller because energy is stateful and implemented in Module 1.3.

- [ ] **Step 3: Validate builder output against processed schema**

In the test, call:

```python
validate_payload(
    "processed-telemetry.v1.schema.json",
    result.model_dump(mode="json"),
)
```

- [ ] **Step 4: Run all Module 1.2 tests**

```bash
pytest tests/contracts tests/domain -v
ruff check src tests
ruff format --check src tests
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/src/biovolt_backend/domain/processing.py backend/tests/domain/test_processing.py
git commit -m "feat: build processed telemetry from raw frames"
```

## Module 1.2 Exit Criteria

- [ ] Phase 0 canonical raw example validates through JSON Schema and Pydantic.
- [ ] Processed model serialization validates against the Phase 0 processed schema.
- [ ] Current formula is unit-tested in µA.
- [ ] Power formula is unit-tested in µW.
- [ ] OD680 is dark/blank corrected and returns `None` for invalid references.
- [ ] No biomass/carbon number is invented without calibration.
- [ ] Processing is pure except for caller-supplied timestamp and cumulative-energy state.
- [ ] All contract/domain tests and Ruff checks pass.
