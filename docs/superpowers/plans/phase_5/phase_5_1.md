# Phase 5.1: Calibration Math and Fit Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize BioVolt calibration validation and scientific derivations in pure backend functions with explicit eligibility and fit diagnostics.

**Architecture:** Pure Python domain functions receive raw measurement values plus one immutable calibration revision and return values with quality metadata. Regression fitting is deterministic and small enough to implement with Python/numpy or a reviewed explicit least-squares helper. The PWA never duplicates these formulas.

**Tech Stack:** Python 3.11+, Pydantic, `math`, optional NumPy if added explicitly, pytest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Scientific functions are pure and independently unit tested.
- No function silently substitutes default calibration values.
- No function silently clamps invalid OD transmission ratios.
- No arbitrary R-squared acceptance threshold is hard-coded.
- At least three distinct calibration points are required for a complete biomass linear fit.
- Fit diagnostics are retained even when fit quality is poor.
- Units are explicit in names.

---

### Task 1: Define calibration domain types and validation

**Files:**
- Create: `backend/src/biovolt_backend/calibration/types.py`
- Create: `backend/src/biovolt_backend/calibration/validation.py`
- Create: `backend/tests/calibration/test_validation.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ElectricalCalibration:
    load_resistance_ohm: float
    ads1115_offset_mv: float

@dataclass(frozen=True)
class OpticalCalibration:
    dark_raw: float
    blank_raw: float

@dataclass(frozen=True)
class BiomassCalibration:
    model_type: Literal["linear"]
    slope_g_l_per_od: float
    intercept_g_l: float
    point_count: int
    r_squared: float | None
    rmse_g_l: float | None
    od_min: float
    od_max: float

@dataclass(frozen=True)
class ReactorCalibration:
    reactor_volume_l: float
    co2_per_dry_biomass_g_per_g: float
```

Validation rules:
- load resistance finite and > 0
- ADC offset finite
- blank and dark finite, blank > dark
- biomass slope/intercept finite, slope > 0
- point count >= 3 for complete biomass model
- OD min/max finite and min < max
- reactor volume finite and > 0
- CO2 factor finite and > 0

- [ ] **Step 1: Write failing validation tests for every invalid boundary**
- [ ] **Step 2: Implement structured validation result with field-specific errors**
- [ ] **Step 3: Add valid complete-profile test**
- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/calibration/test_validation.py -v
git add src/biovolt_backend/calibration/types.py src/biovolt_backend/calibration/validation.py tests/calibration/test_validation.py
git commit -m "feat: validate BioVolt calibration parameters"
```

---

### Task 2: Implement calibrated electrical calculations

**Files:**
- Create: `backend/src/biovolt_backend/domain/calibrated_electrical.py`
- Create: `backend/tests/domain/test_calibrated_electrical.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ElectricalResult:
    corrected_voltage_mv: float | None
    current_ua: float | None
    power_uw: float | None
    eligible: bool
    reason: str | None


def derive_electrical(
    measured_voltage_mv: float | None,
    calibration: ElectricalCalibration | None,
) -> ElectricalResult: ...
```

Formula:

```text
V_corrected_mv = V_measured_mv - offset_mv
I_uA = V_corrected_mv * 1000 / R_ohm
P_uW = V_corrected_mv^2 / R_ohm
```

- [ ] **Step 1: Write exact numeric unit tests**
- [ ] **Step 2: Write missing calibration and missing voltage tests**
- [ ] **Step 3: Verify negative corrected voltage is preserved and power remains squared/non-negative**
- [ ] **Step 4: Implement function**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/domain/test_calibrated_electrical.py -v
git add src/biovolt_backend/domain/calibrated_electrical.py tests/domain/test_calibrated_electrical.py
git commit -m "feat: derive calibrated BioVolt electrical metrics"
```

---

### Task 3: Implement OD680 derivation with explicit quality result

**Files:**
- Create: `backend/src/biovolt_backend/domain/optical_density.py`
- Create: `backend/tests/domain/test_optical_density.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class OdResult:
    od680: float | None
    transmission_ratio: float | None
    eligible: bool
    reason: str | None


def derive_od680(sample_raw: float | None, calibration: OpticalCalibration | None) -> OdResult: ...
```

Reason codes:

```text
missing_sample
missing_calibration
invalid_blank_dark
nonpositive_corrected_sample
invalid_transmission
```

- [ ] **Step 1: Write known-ratio test, e.g. ratio 0.1 -> OD 1.0**
- [ ] **Step 2: Write blank==dark and sample<=dark tests returning null**
- [ ] **Step 3: Write sample>blank test and preserve mathematically valid negative OD rather than clamping**
- [ ] **Step 4: Implement using `math.log10`**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/domain/test_optical_density.py -v
git add src/biovolt_backend/domain/optical_density.py tests/domain/test_optical_density.py
git commit -m "feat: derive BioVolt OD680 with explicit eligibility"
```

---

### Task 4: Implement linear OD-to-biomass fitting

**Files:**
- Create: `backend/src/biovolt_backend/calibration/biomass_fit.py`
- Create: `backend/tests/calibration/test_biomass_fit.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class BiomassCalibrationPoint:
    od680: float
    dry_biomass_g_l: float

@dataclass(frozen=True)
class LinearFitResult:
    slope_g_l_per_od: float
    intercept_g_l: float
    r_squared: float | None
    rmse_g_l: float
    point_count: int
    unique_od_count: int
    od_min: float
    od_max: float


def fit_linear_biomass(points: Sequence[BiomassCalibrationPoint]) -> LinearFitResult: ...
```

Rules:
- >=3 points
- >=3 distinct OD values
- all finite
- dry biomass values >= 0
- reject zero OD variance
- slope must be > 0 for a scientifically usable BioVolt profile
- calculate unrounded coefficients internally

- [ ] **Step 1: Write exact linear dataset test**
- [ ] **Step 2: Write noisy dataset diagnostics test**
- [ ] **Step 3: Write duplicate-OD/zero-variance/negative-biomass rejection tests**
- [ ] **Step 4: Implement least-squares fit, R², RMSE, observed range**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/calibration/test_biomass_fit.py -v
git add src/biovolt_backend/calibration/biomass_fit.py tests/calibration/test_biomass_fit.py
git commit -m "feat: fit BioVolt OD to dry biomass calibration"
```

---

### Task 5: Implement biomass and CO2 derivation

**Files:**
- Create: `backend/src/biovolt_backend/domain/biomass.py`
- Create: `backend/tests/domain/test_biomass.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class BiomassResult:
    biomass_g_l: float | None
    dry_biomass_g: float | None
    extrapolated: bool
    eligible: bool
    reason: str | None

@dataclass(frozen=True)
class CarbonResult:
    biomass_delta_g: float | None
    estimated_co2_biofixed_g: float | None
    eligible: bool
    reason: str | None
```

Rules:
- biomass concentration uses linear profile
- `extrapolated=True` when OD outside `[od_min, od_max]`
- do not force extrapolated result null automatically; expose caveat
- reactor mass requires valid reactor volume
- carbon requires current mass and stored experiment baseline mass
- negative biomass delta remains negative

- [ ] **Step 1: Write in-range and extrapolated biomass tests**
- [ ] **Step 2: Write reactor mass unit test**
- [ ] **Step 3: Write positive and negative biomass-delta carbon tests**
- [ ] **Step 4: Write missing baseline -> null test**
- [ ] **Step 5: Implement and run**

```bash
pytest tests/domain/test_biomass.py -v
```

- [ ] **Step 6: Commit**

```bash
git add src/biovolt_backend/domain/biomass.py tests/domain/test_biomass.py
git commit -m "feat: derive BioVolt biomass and estimated CO2 biofixation"
```

---

### Task 6: Add a consolidated derivation-quality contract

**Files:**
- Create: `backend/src/biovolt_backend/domain/quality.py`
- Create: `backend/tests/domain/test_quality.py`

**Interfaces:**

```python
class DerivationQuality(BaseModel):
    electrical_eligible: bool
    od_eligible: bool
    biomass_eligible: bool
    carbon_eligible: bool
    biomass_extrapolated: bool
    reasons: list[str]
```

- [ ] **Step 1: Write composition tests from missing optical/baseline cases**
- [ ] **Step 2: Implement deterministic reason ordering**
- [ ] **Step 3: Ensure quality metadata contains no judge-facing claim language such as `accurate` or `significant`**
- [ ] **Step 4: Run all calibration/domain tests and commit**

```bash
pytest tests/calibration tests/domain -v
git add src/biovolt_backend/domain/quality.py tests/domain/test_quality.py
git commit -m "feat: expose BioVolt scientific derivation quality"
```

## Module 5.1 Exit Criteria

- [ ] All formulas have explicit units and pure tests.
- [ ] Invalid OD inputs return null with reason.
- [ ] Linear biomass fit requires real calibration points and stores diagnostics.
- [ ] No universal R-squared threshold is invented.
- [ ] Extrapolation is flagged.
- [ ] Negative biomass delta is preserved.
- [ ] CO2 factor is supplied by profile metadata rather than hidden constant.
