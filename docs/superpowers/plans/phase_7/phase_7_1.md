# Phase 7.1: Analytics Domain and Data-Quality Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement BioVolt experiment KPI and data-quality logic as pure, testable backend domain functions before exposing analytics endpoints or dashboard cards.

**Architecture:** Analytics domain functions consume completed experiment metadata and persisted calibrated telemetry rows. They return explicit arm summaries, quality metrics, comparison eligibility, and matched-window KPI values. No HTTP, ORM session, or frontend logic appears in these pure functions.

**Tech Stack:** Python dataclasses/Pydantic, statistics/math, pytest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Every invalid calculation returns null plus reason.
- Never treat missing telemetry as zero-power observation.
- Never interpolate across missing intervals for energy.
- Comparison operates on elapsed time, not unequal full-run durations.
- Synthetic evidence status is carried separately from telemetry source.
- No inferential statistics are implemented in this module.

---

### Task 1: Add immutable experiment evidence class

**Files:**
- Modify: `backend/src/biovolt_backend/config.py`
- Modify: `backend/src/biovolt_backend/experiments/models.py`
- Modify: `backend/src/biovolt_backend/experiments/schemas.py`
- Test: `backend/tests/experiments/test_evidence_class.py`

Setting:

```text
BIOVOLT_EVIDENCE_CLASS=measured|synthetic_demo
```

Rules:
- stamped onto experiment at creation
- visible in experiment reads
- immutable after creation or at minimum after `ready`
- simulator CI/demo deployment explicitly sets `synthetic_demo`
- real-hardware deployment sets `measured`

- [ ] **Step 1: Write measured/synthetic creation tests**
- [ ] **Step 2: Write immutable evidence test**
- [ ] **Step 3: Implement setting validation and experiment stamp**
- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/experiments/test_evidence_class.py -v
git add src/biovolt_backend/config.py src/biovolt_backend/experiments tests/experiments/test_evidence_class.py
git commit -m "feat: stamp BioVolt experiment evidence provenance"
```

---

### Task 2: Define analytics input/output types and elapsed-window selection

**Files:**
- Create: `backend/src/biovolt_backend/analytics/types.py`
- Create: `backend/src/biovolt_backend/analytics/windows.py`
- Create: `backend/src/biovolt_backend/analytics/__init__.py`
- Test: `backend/tests/analytics/test_windows.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class AnalyticsSample:
    received_at: datetime
    sequence: int
    uptime_ms: int
    power_uw: float | None
    cumulative_energy_mj: float | None
    od680: float | None
    biomass_g_l: float | None
    dry_biomass_g: float | None
    temperature_c: float | None
    grow_led_pwm: int
    mixer_on: bool
    quality: DerivationQuality

@dataclass(frozen=True)
class MatchedWindow:
    duration_s: float
    passive_samples: tuple[AnalyticsSample, ...]
    adaptive_samples: tuple[AnalyticsSample, ...]
```

- [ ] **Step 1: Write equal-duration selection test**
- [ ] **Step 2: Write unequal arm duration test using shorter common duration**
- [ ] **Step 3: Write no-overlap/zero-duration rejection test**
- [ ] **Step 4: Implement elapsed-time selection without interpolation**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/analytics/test_windows.py -v
git add src/biovolt_backend/analytics tests/analytics/test_windows.py
git commit -m "feat: select matched BioVolt experiment windows"
```

---

### Task 3: Implement telemetry gap and coverage metrics

**Files:**
- Create: `backend/src/biovolt_backend/analytics/quality.py`
- Create: `backend/tests/analytics/test_quality.py`

Settings:

```text
analytics_gap_threshold_s = 2.5
minimum_power_coverage_fraction = 0.80
```

These are operational quality defaults and must be configurable.

**Interfaces:**

```python
@dataclass(frozen=True)
class ArmQuality:
    sample_count: int
    valid_power_sample_count: int
    power_coverage_fraction: float
    gap_count: int
    gap_seconds: float
    telemetry_gap_fraction: float
    maximum_gap_seconds: float
    reboot_detected: bool
    biomass_extrapolation_fraction: float | None
    reasons: tuple[str, ...]
```

Coverage calculation uses expected sample opportunity from nominal persistence interval, bounded by matched window duration, with formula documented in code/tests. Gap seconds count only excess time beyond the configured gap threshold so normal timing jitter is not exaggerated.

- [ ] **Step 1: Write no-gap 1 Hz series test**
- [ ] **Step 2: Write 10-second missing interval test**
- [ ] **Step 3: Write invalid-power coverage test**
- [ ] **Step 4: Write uptime-decrease reboot detection test**
- [ ] **Step 5: Implement and run**

```bash
pytest tests/analytics/test_quality.py -v
git add src/biovolt_backend/analytics/quality.py tests/analytics/test_quality.py
git commit -m "feat: measure BioVolt analytics coverage and telemetry gaps"
```

---

### Task 4: Implement arm-level electrical and control metrics

**Files:**
- Create: `backend/src/biovolt_backend/analytics/metrics.py`
- Create: `backend/tests/analytics/test_metrics.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ElectricalArmMetrics:
    mean_power_uw: float | None
    median_power_uw: float | None
    min_power_uw: float | None
    max_power_uw: float | None
    energy_mj: float | None
    energy_per_hour_mj_h: float | None

@dataclass(frozen=True)
class ControlArmMetrics:
    mean_grow_led_pwm: float | None
    led_pwm_change_count: int
    mixer_on_fraction: float | None
```

Energy rule:
- require non-null cumulative energy at first/last selected rows
- require monotonic uptime and nondecreasing cumulative energy within window
- energy = last - first
- reset/decrease -> null with quality reason

- [ ] **Step 1: Write known mean/median/control duty tests**
- [ ] **Step 2: Write cumulative-energy difference test**
- [ ] **Step 3: Write energy reset/decrease invalid test**
- [ ] **Step 4: Implement metric functions**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/analytics/test_metrics.py -v
git add src/biovolt_backend/analytics/metrics.py tests/analytics/test_metrics.py
git commit -m "feat: calculate BioVolt arm electrical and control metrics"
```

---

### Task 5: Implement scientific outcome summary

**Files:**
- Create: `backend/src/biovolt_backend/analytics/scientific.py`
- Create: `backend/tests/analytics/test_scientific.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class ScientificArmMetrics:
    starting_od680: float | None
    ending_od680: float | None
    od680_change: float | None
    starting_biomass_g_l: float | None
    ending_biomass_g_l: float | None
    biomass_concentration_change_g_l: float | None
    starting_dry_biomass_g: float | None
    ending_dry_biomass_g: float | None
    biomass_delta_g: float | None
    estimated_co2_biofixed_g: float | None
```

Use first/last eligible values in matched/full requested window and preserve null if calibration/baseline eligibility is absent.

- [ ] **Step 1: Write valid start/end test**
- [ ] **Step 2: Write missing-biomass eligibility test**
- [ ] **Step 3: Write negative biomass-delta preservation test**
- [ ] **Step 4: Implement and run**

```bash
pytest tests/analytics/test_scientific.py -v
git add src/biovolt_backend/analytics/scientific.py tests/analytics/test_scientific.py
git commit -m "feat: summarize BioVolt scientific experiment outcomes"
```

---

### Task 6: Implement Passive-vs-Adaptive comparison eligibility and KPI

**Files:**
- Create: `backend/src/biovolt_backend/analytics/comparison.py`
- Create: `backend/tests/analytics/test_comparison.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class EnergyComparison:
    eligible: bool
    passive_energy_mj: float | None
    adaptive_energy_mj: float | None
    gain_pct: float | None
    common_duration_s: float | None
    reasons: tuple[str, ...]
```

Eligibility reasons include:

```text
wrong_modes
not_completed
synthetic_demo
no_common_duration
insufficient_passive_coverage
insufficient_adaptive_coverage
device_reboot
nonpositive_passive_energy
missing_energy
```

- [ ] **Step 1: Write known +20% gain test**
- [ ] **Step 2: Write negative gain test**
- [ ] **Step 3: Write passive zero denominator test**
- [ ] **Step 4: Write synthetic evidence block test**
- [ ] **Step 5: Write coverage/reboot block tests**
- [ ] **Step 6: Implement exact formula and deterministic reason ordering**
- [ ] **Step 7: Run all analytics tests and commit**

```bash
pytest tests/analytics -v
git add src/biovolt_backend/analytics/comparison.py tests/analytics/test_comparison.py
git commit -m "feat: compare Passive and Adaptive BioVolt energy fairly"
```

## Module 7.1 Exit Criteria

- [ ] Evidence class is experiment provenance, not raw telemetry source branching.
- [ ] Matched window uses common elapsed duration.
- [ ] Coverage/gap formulas are explicit/configurable.
- [ ] Energy rejects reboot/reset rather than silently stitching sessions.
- [ ] Gain requires positive Passive energy.
- [ ] Synthetic demo data cannot produce a measured headline KPI.
- [ ] Scientific summary preserves nulls and Phase 5 semantics.
- [ ] No inferential-statistics implementation exists in MVP analytics.
