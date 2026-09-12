# Phase 5 Overview: Calibration Profiles and Scientific Quantification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every BioVolt derived scientific value reproducible from an immutable, versioned calibration profile and prevent biomass/carbon claims when calibration provenance or experiment baselines are incomplete.

**Architecture:** Calibration becomes a first-class backend domain. A profile contains electrical, optical, biomass, reactor-volume, and scientific conversion metadata; edits create revisions rather than mutating historical profiles. Experiments bind an immutable calibration revision at start, and FastAPI uses that snapshot for all experiment-derived current, power, OD680, biomass, and estimated CO2 values. The PWA provides a guided calibration wizard but never performs scientific calculations independently.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x async ORM, SQLite, Python numerical utilities, React/TypeScript, Recharts for fit visualization, pytest/Vitest.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 4 experiment lifecycle and operator-protected writes.

## Scientific Eligibility Rules

A value is not judge-facing merely because the formula can run.

```text
Raw measurement available
      |
      v
Calibration inputs valid
      |
      v
Profile revision active/bound
      |
      v
Experiment baseline available where required
      |
      v
Derived value eligible
```

If any required input is invalid or absent, return `null` plus an explicit quality/reason field. Never substitute zero or an arbitrary fallback coefficient.

## Calibration Profile Contents

Required electrical fields:

```text
load_resistance_ohm > 0
ads1115_offset_mv finite
```

Required optical fields for OD680:

```text
optical_dark_raw
optical_blank_raw
blank > dark
```

Required biomass fields for biomass conversion:

```text
model_type = linear
slope_g_l_per_od
intercept_g_l
calibration_point_count
r_squared
rmse_g_l
```

Required reactor/scientific fields for reactor biomass and CO2 estimate:

```text
reactor_volume_l > 0
co2_per_dry_biomass_g_per_g > 0
```

Default scientific conversion may be `1.83 g CO2 / g dry biomass` only when explicitly documented as the selected biomass-stoichiometry assumption. It is metadata in the calibration profile, not a hidden constant.

Optional metadata:

```text
name
description
created_at
created_by operator label if available
reference/source notes
temperature_offset_c
lux_offset
```

Optional sensor offsets are applied only if the field is explicitly present and validated.

## Approved Calculation Chain

### Corrected BPV voltage

```text
corrected_voltage_mv = measured_bpv_voltage_mv - ads1115_offset_mv
```

Do not silently clamp negative corrected values. Preserve the value for audit and let downstream power/current rules handle physical eligibility explicitly.

### Current

```text
current_ua = corrected_voltage_mv * 1000 / load_resistance_ohm
```

### Power

```text
power_uw = corrected_voltage_mv^2 / load_resistance_ohm
```

### OD680

```text
transmission_ratio =
  (sample_raw - dark_raw) / (blank_raw - dark_raw)

OD680 = -log10(transmission_ratio)
```

Eligibility:
- `blank_raw - dark_raw > 0`
- `sample_raw - dark_raw > 0`
- transmission ratio finite and > 0

Do not clamp an invalid ratio into `(0,1]` just to force a plausible OD.

### Biomass concentration

For MVP linear calibration:

```text
biomass_g_l = slope_g_l_per_od * OD680 + intercept_g_l
```

A profile needs at least three distinct calibration points before the wizard can mark the biomass model complete. Fit quality is reported, not hidden behind an invented universal R-squared threshold.

### Reactor dry biomass mass

```text
dry_biomass_g = biomass_g_l * reactor_volume_l
```

### Biomass gain

```text
biomass_delta_g = current_dry_biomass_g - experiment_baseline_dry_biomass_g
```

Negative delta remains negative. Do not force it to zero.

### Estimated CO2 biofixed into biomass

```text
estimated_co2_biofixed_g =
  biomass_delta_g * co2_per_dry_biomass_g_per_g
```

Dashboard wording remains exactly **Estimated CO2 biofixed into biomass**. This does not imply permanent sequestration or direct room-air CO2 removal.

---

## Calibration Revision Model

```text
Calibration Profile identity
       |
       +-- revision 1 immutable
       +-- revision 2 immutable
       +-- revision 3 immutable
```

Editing a profile creates a new revision. Existing experiments retain the revision/snapshot they started with.

Active default profile is only a convenience for Monitor mode and new experiment setup. It must not retroactively change historical experiment calculations.

---

## Experiment Binding

Before an experiment may move `ready -> starting` in Phase 5:

```text
selected calibration revision exists
revision is scientifically valid for requested outputs
reactor volume present when biomass/carbon is requested
```

At experiment start, persist an immutable calibration snapshot or immutable revision reference whose contents can no longer change.

Baseline rules:
- experiment arm baseline is the first eligible processed sample after the experiment reaches `running`, unless the operator intentionally captures a baseline immediately before start through the defined endpoint
- baseline timestamp and source telemetry sequence are stored
- biomass/carbon remain unavailable until baseline exists

---

## Module Map

### Module 5.1: Calibration Math and Fit Core
Plan: `docs/superpowers/plans/phase_5/phase_5_1.md`

Produces:
- pure calibration validation
- corrected electrical calculations
- OD680 eligibility logic
- linear OD-to-biomass fitting
- fit diagnostics
- biomass/CO2 pure functions

### Module 5.2: Calibration Persistence, Revisioning, and API
Plan: `docs/superpowers/plans/phase_5/phase_5_2.md`

Produces:
- calibration profile/revision tables
- immutable revision service
- activation/default-profile semantics
- capture/read/write REST endpoints
- operator protection

### Module 5.3: Experiment Calibration Binding and Processing Integration
Plan: `docs/superpowers/plans/phase_5/phase_5_3.md`

Produces:
- experiment-bound revision/snapshot
- baseline capture
- calibrated telemetry processing
- explicit derivation eligibility/reason fields
- reproducible historical experiment values

### Module 5.4: PWA Calibration Wizard
Plan: `docs/superpowers/plans/phase_5/phase_5_4.md`

Produces:
- prerequisite checks
- electrical calibration steps
- optical dark/blank capture
- biomass calibration-point entry
- fit-review visualization
- review/activate flow
- experiment profile selection

### Module 5.5: Calibration and Scientific Data-Quality Acceptance
Plan: `docs/superpowers/plans/phase_5/phase_5_5.md`

Produces:
- independent formula spot checks
- revision immutability tests
- invalid-calibration null behavior
- CSV/provenance checks
- calibration HIL checklist
- Phase 5 regression gate

---

## Product Design Requirements

Calibration is a guided workflow, not a dense configuration form.

Recommended wizard sequence:

```text
1. Prerequisites and sensor health
2. Electrical/load setup
3. Optical dark capture
4. Optical blank-medium capture
5. Biomass calibration points
6. Fit review
7. Reactor/scientific metadata
8. Review and activate
```

Every step shows:
- what physical sample/setup is required
- what will be captured
- the latest raw value and timestamp
- whether the prerequisite is valid
- a clear next action

The wizard must not silently advance on stale telemetry.

## Data Analytics Requirements

Calibration fit diagnostics must include:
- point count
- unique OD count
- slope
- intercept
- R-squared
- RMSE in g/L
- observed OD range
- observed biomass range

The UI/report must not label a model `accurate` based solely on R-squared. It should expose the diagnostics and calibration range. Extrapolated experiment OD values outside the calibrated OD range are allowed only with an explicit `extrapolated=true` quality flag and visible caveat.

## Planned Commit Sequence

1. `feat: add BioVolt calibration math and fit diagnostics`
2. `feat: persist immutable calibration revisions`
3. `feat: bind calibration snapshots to experiments`
4. `feat: add BioVolt calibration wizard`
5. `test: validate BioVolt scientific calibration provenance`

## Phase 5 Exit Criteria

- [ ] Electrical derivations use calibrated load resistance and ADC offset.
- [ ] OD680 invalid inputs return null rather than clamped values.
- [ ] Biomass requires a valid, versioned calibration model.
- [ ] Biomass model stores point count, fit diagnostics, and calibration range.
- [ ] Calibration edits create new revisions instead of mutating old experiments.
- [ ] Each running experiment is bound to one immutable calibration revision/snapshot.
- [ ] Baseline telemetry sequence/timestamp is auditable.
- [ ] Biomass and CO2 remain null until a valid baseline exists.
- [ ] Negative biomass delta is preserved rather than silently clamped.
- [ ] CO2 conversion factor is explicit profile metadata.
- [ ] Dashboard wording is `Estimated CO2 biofixed into biomass`.
- [ ] Out-of-range OD conversion is visibly flagged as extrapolation.
- [ ] PWA wizard refuses stale/missing raw capture inputs.
- [ ] Existing Phase 0 to 4 regression suites remain green.

## Handoff to Phase 6

Phase 6 enables the ESP32 local adaptive Perturb & Observe control loop. It uses the already-proven safety, experiment, command, and calibrated measurement substrate but does not itself compute or claim A/B improvement.
