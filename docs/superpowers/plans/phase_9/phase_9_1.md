# Phase 9.1: Scientific, Electrical, Calibration, and Claim-Integrity Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task-by-task. Apply Ponytail product-design reasoning wherever scientific eligibility is translated into visible copy, units, badges, or unavailable states. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently validate that BioVolt's electrical, optical-density, biomass, CO2, energy, and calibration-derived outputs are numerically correct, traceable, scientifically eligible, and presented with truthful judge-facing terminology.

**Architecture:** Production outputs are recomputed from stored raw telemetry and calibration revisions using an independent validation implementation that does not import production calculation modules. Validation checks formulas, units, provenance, null/eligibility behavior, physical reference points, and production copy/labels.

**Tech Stack:** Python, CSV/SQLite reads, pytest, independent numeric helpers, browser/API checks, physical bench measurements where required.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints

- Independent validators do not import production scientific-calculation functions.
- A calculation can be numerically possible but scientifically ineligible; eligibility is validated separately.
- CO2 wording remains `Estimated CO2 biofixed into biomass`, not permanent sequestration/removal.
- Missing/invalid calibration yields unavailable derived values rather than guessed constants.
- Synthetic/demo evidence never satisfies a measured-evidence release claim.
- Displayed units match the calculation/storage contract exactly.
- BH1750 remains `Light (lux)`, never mislabeled as PAR.

---

### Task 1: Independent electrical recomputation

**Files:**
- Create: `scripts/release/validate_electrical.py`
- Create: `tests/release/test_validate_electrical.py`

- [ ] Independently implement `current_ua = voltage_mv * 1000 / resistance_ohm`.
- [ ] Independently implement `power_uw = voltage_mv^2 / resistance_ohm`.
- [ ] Test 438.2 mV across 100000 ohm -> 4.382 uA and approximately 1.920 uW.
- [ ] Load persisted telemetry and exact calibration revision/load resistance used by the experiment.
- [ ] Recompute every eligible row.
- [ ] Compare production and independent results with frozen tolerance based on stored precision.
- [ ] Fail on unit mismatch, invalid resistance, hidden fallback constant, or calibration-revision mismatch.
- [ ] Commit `test: independently validate BioVolt electrical metrics`.

---

### Task 2: Validate energy integration and continuity handling

**Files:**
- Create: `scripts/release/validate_energy.py`
- Test: `tests/release/test_validate_energy.py`

- [ ] Implement independent trapezoidal integration using device `uptime_ms`.
- [ ] Test contiguous samples, sequence gaps, reboot/uptime reset, duplicate/out-of-order frames.
- [ ] Require no integration across unobserved telemetry gaps.
- [ ] Recompute experiment cumulative energy and compare with production result.
- [ ] Fail if cumulative energy decreases in a continuous valid segment except an explicit experiment reset.
- [ ] Verify experiment/window boundaries are not crossed accidentally.
- [ ] Commit `test: independently validate BioVolt energy integration`.

---

### Task 3: Validate OD680 optical math and provenance

**Files:**
- Create: `scripts/release/validate_od680.py`
- Test: `tests/release/test_validate_od680.py`

Independent formula:

```text
OD680 = -log10((I_sample - I_dark) / (I_blank - I_dark))
```

- [ ] Test blank -> OD approximately 0.
- [ ] Test corrected 10% transmission -> OD approximately 1.
- [ ] Reject non-positive corrected numerator/denominator domains.
- [ ] Verify each displayed OD680 references the exact calibration revision used by the experiment.
- [ ] Verify missing/invalid optical calibration produces `null`/Unavailable rather than guessed OD.
- [ ] Verify BPW34 acquisition health is not misrepresented as calibration validity.
- [ ] Commit `test: independently validate BioVolt OD680`.

---

### Task 4: Validate biomass and carbon eligibility

**Files:**
- Create: `scripts/release/validate_biomass_carbon.py`
- Test: `tests/release/test_validate_biomass_carbon.py`

- [ ] Recompute biomass concentration from persisted OD-to-biomass regression coefficients.
- [ ] Verify regression fit/revision satisfies Phase 5 eligibility criteria.
- [ ] Recompute total biomass using recorded reactor volume.
- [ ] Recompute biomass delta from the Phase 5 experiment baseline definition.
- [ ] Recompute `estimated_co2_biofixed_g = biomass_delta_g * 1.83` only when all required provenance is valid.
- [ ] Verify negative/invalid baseline cases follow Phase 5 rules rather than being clipped into positive claims.
- [ ] Verify measured-evidence requirement for judge-facing measured claims.
- [ ] Commit `test: validate BioVolt biomass and carbon eligibility`.

---

### Task 5: Validate calibration revision immutability and experiment pinning

**Files:**
- Create: `scripts/release/validate_calibration_provenance.py`
- Test: `tests/release/test_validate_calibration_provenance.py`

- [ ] Verify completed experiment references a concrete immutable calibration revision ID.
- [ ] Verify later calibration edits/revisions do not silently alter historical experiment analytics.
- [ ] Verify load resistance, optical dark/blank, OD-biomass coefficients, volume, and offsets resolve from the pinned revision.
- [ ] Verify incomplete revisions cannot be activated for derived metrics requiring missing fields.
- [ ] Fail any historical result whose provenance cannot be reconstructed.
- [ ] Commit `test: validate BioVolt calibration provenance immutability`.

---

### Task 6: Bench sanity checks against physical references

**Files:**
- Create: `docs/release/scientific-bench-check.md`
- Create: `docs/release/scientific-validation-schema.md`

- [ ] Check precision load resistor with a trusted multimeter and record measured value/tolerance in calibration evidence.
- [ ] Check ADS1115 zero/known-voltage response with trusted source or meter-assisted reference.
- [ ] Record BPW34 dark and blank readings using the actual optical fixture.
- [ ] Verify 680 nm probe LED pulse timing/geometry is repeatable enough for the intended hackathon measurement, without claiming laboratory certification.
- [ ] Compare DS18B20/BH1750 plausibility to reference instrument or documented ambient comparison.
- [ ] Record pass/fail and notes in release evidence pack.
- [ ] Commit `docs: add BioVolt scientific bench release checks`.

---

### Task 7: Ponytail scientific claim and unit audit

**Files:**
- Create: `scripts/release/validate_scientific_copy.py`
- Create: `docs/product/scientific-claim-copy.md`
- Test: production PWA and safe public Results surfaces

Audit terms/units across Overview, Live Data, Results, experiment history, export metadata, and public judge view.

Required wording examples:

```text
BPV Voltage (mV)
Current (uA)
Power (uW)
Cumulative Energy (mJ)
OD680
Estimated Biomass (g/L or g, context explicit)
Estimated CO2 biofixed into biomass (g)
Light (lux)
Simulation / demo data
Unavailable
```

Forbidden/misleading examples:

```text
CO2 permanently removed
CO2 sequestered permanently
PAR (unless a PAR sensor is actually added)
AI optimized (if the implemented controller is P&O and not ML)
measured gain on synthetic-only evidence
0% when a comparison is actually ineligible
```

- [ ] Search production frontend/backend export-copy sources for forbidden wording.
- [ ] Verify displayed unit follows the numerical field.
- [ ] Verify `Unavailable` carries reason where Phase 5/7 eligibility provides one.
- [ ] Verify uncertainty/quality details are accessible without overwhelming headline hierarchy.
- [ ] Commit `test: validate BioVolt scientific claim integrity`.

---

### Task 8: Scientific release gate

**Files:**
- Create: `scripts/release/phase9_science_gate.py`

Aggregate:
- electrical
- energy continuity
- OD680
- biomass/carbon
- calibration provenance
- physical bench checks
- scientific copy/unit integrity

- [ ] Emit machine-readable JSON plus concise terminal summary.
- [ ] Classify any formula/provenance/eligibility/copy error affecting judge-facing claims as BLOCKER.
- [ ] Require zero BLOCKER findings.
- [ ] Commit `test: add BioVolt scientific release gate`.

## Exit Criteria

- [ ] Independent electrical values agree with production values.
- [ ] Energy integration does not bridge missing telemetry.
- [ ] OD680 uses valid dark/blank calibration and correct formula.
- [ ] Biomass/CO2 claims require valid regression, volume, baseline, calibration provenance, and eligible evidence.
- [ ] Historical experiments remain pinned to immutable calibration revisions.
- [ ] Physical bench sanity checks are documented.
- [ ] Product copy and units do not overclaim or mislabel measurements.
- [ ] Scientific gate reports zero BLOCKER findings.
