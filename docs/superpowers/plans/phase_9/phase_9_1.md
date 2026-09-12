# Phase 9.1: Scientific, Electrical, and Calibration Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently validate that BioVolt's electrical, optical-density, biomass, CO2, energy, and calibration-derived outputs are numerically correct, traceable, and scientifically eligible for display.

**Architecture:** Production outputs are recomputed from stored raw telemetry and calibration revisions using an independent validation implementation that does not import the production calculation modules. Validation checks formulas, units, provenance, null/eligibility behavior, and known physical test points.

**Tech Stack:** Python, CSV/SQLite reads, pytest, independent numeric helpers, physical bench measurements where required.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints
- Independent validators must not import production scientific-calculation functions.
- A calculation can be numerically possible but scientifically ineligible; eligibility is validated separately.
- CO2 wording remains `estimated CO2 biofixed into biomass`, not permanent sequestration.
- Missing/invalid calibration yields unavailable derived values rather than guessed constants.

---

### Task 1: Independent electrical recomputation

**Files:**
- Create: `scripts/release/validate_electrical.py`
- Create: `tests/release/test_validate_electrical.py`

- [ ] Define independent formulas for `current_ua = voltage_mv * 1000 / resistance_ohm` and `power_uw = voltage_mv^2 / resistance_ohm`.
- [ ] Write known-value tests including 438.2 mV across 100000 ohm -> 4.382 uA and approximately 1.920 uW.
- [ ] Load persisted telemetry plus calibration load resistance and recompute every eligible stored row.
- [ ] Compare production vs independent values using strict floating-point tolerance appropriate to stored precision.
- [ ] Fail on unit mismatches, negative impossible resistance, or silently substituted defaults.
- [ ] Commit `test: independently validate BioVolt electrical metrics`.

### Task 2: Validate energy integration and continuity handling

**Files:**
- Create: `scripts/release/validate_energy.py`
- Test: `tests/release/test_validate_energy.py`

- [ ] Implement independent trapezoidal integration using device `uptime_ms`.
- [ ] Write tests for contiguous samples, sequence gaps, reboot/uptime reset, duplicate/out-of-order frames.
- [ ] Require no integration across an unobserved telemetry gap.
- [ ] Recompute experiment cumulative energy from stored raw/processed evidence and compare with production result.
- [ ] Fail if cumulative energy decreases within a continuous valid boot segment except on explicitly modeled experiment reset.
- [ ] Commit `test: independently validate BioVolt energy integration`.

### Task 3: Validate OD680 optical math and calibration provenance

**Files:**
- Create: `scripts/release/validate_od680.py`
- Test: `tests/release/test_validate_od680.py`

- [ ] Independently implement dark-corrected OD680: `-log10((I_sample-I_dark)/(I_blank-I_dark))`.
- [ ] Test known synthetic points including blank -> OD near 0 and 10 percent transmission -> OD near 1 after correction.
- [ ] Reject invalid domains where corrected sample or denominator is non-positive.
- [ ] Verify each displayed OD680 references the exact active calibration revision used by the experiment.
- [ ] Verify missing/invalid optical calibration makes OD680 unavailable rather than estimated from arbitrary constants.
- [ ] Commit `test: independently validate BioVolt OD680`.

### Task 4: Validate biomass and CO2 eligibility

**Files:**
- Create: `scripts/release/validate_biomass_carbon.py`
- Test: `tests/release/test_validate_biomass_carbon.py`

- [ ] Recompute biomass concentration from the persisted OD-to-biomass regression coefficients.
- [ ] Recompute total biomass using the recorded reactor volume.
- [ ] Recompute biomass delta relative to the experiment baseline defined by Phase 5.
- [ ] Recompute `estimated_co2_biofixed_g = biomass_delta_g * 1.83` only when all required provenance is valid.
- [ ] Verify negative/invalid baseline cases follow the Phase 5 eligibility rules rather than being clipped into misleading positive claims.
- [ ] Verify UI/API copy does not say permanent sequestration/removal.
- [ ] Commit `test: validate BioVolt biomass and carbon claims`.

### Task 5: Bench sanity checks against physical references

**Files:**
- Create: `docs/release/scientific-bench-check.md`
- Create: `release-evidence/scientific-validation.example.json` documentation schema only, not live secrets/data.

- [ ] Check the precision load resistor with a trusted multimeter and record measured value/tolerance in the active calibration revision.
- [ ] Check ADS1115 zero/known-voltage response with a trusted source or meter-assisted reference.
- [ ] Record BPW34 dark and blank measurements using the actual optical fixture.
- [ ] Verify DS18B20 and BH1750 readings are plausible against a reference instrument or documented ambient comparison, without pretending this is laboratory certification.
- [ ] Record pass/fail and measurement notes in the release evidence pack.
- [ ] Commit `docs: add BioVolt scientific bench release checks`.

### Task 6: Scientific release gate

**Files:**
- Create: `scripts/release/phase9_science_gate.py`

- [ ] Aggregate electrical, energy, OD680, biomass, CO2, calibration provenance, and bench-check results.
- [ ] Emit machine-readable JSON plus concise terminal summary.
- [ ] Classify any calculation/provenance mismatch affecting judge-facing claims as BLOCKER.
- [ ] Require zero BLOCKER findings before release-candidate status.
- [ ] Commit `test: add BioVolt scientific release gate`.

## Exit Criteria
- [ ] Independent electrical values agree with production values.
- [ ] Energy integration does not bridge missing telemetry.
- [ ] OD680 uses valid dark/blank calibration and correct formula.
- [ ] Biomass/CO2 claims require valid regression, volume, baseline, and measured evidence.
- [ ] Physical bench sanity checks are documented.
- [ ] Scientific gate reports zero BLOCKER findings.
