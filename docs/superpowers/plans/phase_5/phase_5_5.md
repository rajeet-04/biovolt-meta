# Phase 5.5: Calibration and Scientific Data-Quality Acceptance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate that BioVolt calibration, provenance, and scientific derivations are numerically correct, reproducible, and honest about invalid or extrapolated data before adaptive control and judge-facing analytics are added.

**Architecture:** Acceptance combines deterministic backend unit/integration tests, independent formula recomputation from exported data, and real-hardware calibration checks. The validation target is not only code correctness but claim eligibility: every derived value must trace back to raw measurement, immutable calibration revision, and experiment baseline where required.

**Tech Stack:** pytest, CSV/Python spot-check script, real ESP32/HIL, PWA tests.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Do not approve Phase 5 based only on UI screenshots.
- Independent recomputation must not call the same production derivation helper under test.
- Calibration fit diagnostics must be reproduced from saved raw points.
- Invalid source data must remain null, not become zeros.
- No claim uses `sequestered`, `removed permanently`, or equivalent wording.
- The validation report distinguishes blockers from caveats.

---

### Task 1: Add independent calibration spot-check script

**Files:**
- Create: `scripts/validate_phase5_calibration.py`
- Create: `scripts/phase5_validation.md`

Script inputs:
- exported calibration revision JSON or API response saved locally
- optional experiment telemetry CSV

Independent calculations implement directly in script:

```text
corrected voltage
current
power
OD680
linear fit coefficients
R²
RMSE
biomass concentration
reactor biomass
biomass delta
estimated CO2 biofixed
```

Do not import production `biovolt_backend.domain.*` calculation functions.

- [ ] **Step 1: Implement CLI that accepts revision JSON and optional CSV paths**
- [ ] **Step 2: Print compared stored vs recomputed values with tolerances**
- [ ] **Step 3: Exit non-zero on material mismatch**
- [ ] **Step 4: Add usage/evidence template to validation doc**
- [ ] **Step 5: Commit**

```bash
git add scripts/validate_phase5_calibration.py scripts/phase5_validation.md
git commit -m "test: add independent BioVolt calibration validation"
```

---

### Task 2: Add calibration revision immutability/provenance integration tests

**Files:**
- Create: `backend/tests/integration/test_calibration_provenance.py`

Scenario:

```text
create revision 1
activate revision 1
create/start experiment bound to revision 1
create/activate revision 2
continue experiment telemetry
verify experiment remains revision 1
complete experiment
verify history still resolves revision 1 and stored values
```

- [ ] **Step 1: Implement revision-switch isolation test**
- [ ] **Step 2: Verify baseline retains original sequence/time**
- [ ] **Step 3: Verify revision 1 remains readable after revision 2 activation**
- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/integration/test_calibration_provenance.py -v
git add tests/integration/test_calibration_provenance.py
git commit -m "test: verify BioVolt calibration provenance isolation"
```

---

### Task 3: Add invalid-input scientific null tests

**Files:**
- Create: `backend/tests/integration/test_scientific_nulls.py`

Cases:
- no calibration
- blank == dark
- sample <= dark
- no biomass fit
- no reactor volume
- no baseline
- sensor health false
- extrapolated OD

Expected:
- relevant derived fields null for invalid cases
- reasons present
- extrapolated OD remains calculated only when other inputs valid but flag is true

- [ ] **Step 1: Implement parameterized invalid pipeline tests**
- [ ] **Step 2: Confirm `0.0` is not substituted for unknowns**
- [ ] **Step 3: Confirm negative valid biomass delta remains negative**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/integration/test_scientific_nulls.py -v
git add tests/integration/test_scientific_nulls.py
git commit -m "test: enforce BioVolt scientific null and extrapolation semantics"
```

---

### Task 4: Add PWA scientific-label and caveat tests

**Files:**
- Create: `frontend/tests/calibration/ScientificLabels.test.tsx`
- Modify: relevant telemetry/experiment metric components as implementation requires

Assertions:
- exact label `Estimated CO2 biofixed into biomass`
- no `CO2 sequestered` label
- extrapolated biomass shows visible caveat
- missing baseline renders unavailable state, not `0 g`
- calibration revision shown on experiment detail

- [ ] **Step 1: Write copy/eligibility tests**
- [ ] **Step 2: Add accessible caveat rendering**
- [ ] **Step 3: Run frontend tests and commit**

```bash
cd frontend
npm test -- ScientificLabels
npm run typecheck
npm run lint
git add tests/calibration/ScientificLabels.test.tsx src
git commit -m "test: enforce BioVolt scientific claim labels"
```

---

### Task 5: Execute real-hardware calibration HIL checklist

**Files:**
- Create: `scripts/phase5_calibration_hil.md`

Procedure:

```text
1. Verify ESP32/ADS/BPW34 path healthy.
2. Verify precision load resistor actual measured value with a trusted meter and record it.
3. Capture electrical zero/offset under the defined zero-reference condition.
4. Capture optical dark reference using the defined physical dark setup.
5. Capture blank-medium reference.
6. Confirm blank > dark with useful separation.
7. Collect at least three reviewed OD/dry-biomass reference points when available.
8. Save revision but do not activate until fit review.
9. Independently recalculate fit diagnostics.
10. Activate revision.
11. Start a short experiment and confirm bound revision and baseline.
12. Compare one voltage/current/power observation against independent calculation.
```

The checklist must record actual equipment/reference limitations. If dry biomass reference measurements are not genuinely available, biomass/CO2 remains a demonstrated workflow with incomplete scientific eligibility, not fabricated calibration.

- [ ] **Step 1: Write checklist and evidence table**
- [ ] **Step 2: Execute available physical checks**
- [ ] **Step 3: Mark unavailable reference measurements explicitly as blockers/caveats**
- [ ] **Step 4: Commit checklist only; observed run results belong in PR/release evidence unless intentionally versioned**

```bash
git add scripts/phase5_calibration_hil.md
git commit -m "docs: add BioVolt calibration hardware acceptance"
```

---

### Task 6: Phase 5 regression and validation report

Run:

```bash
pytest shared/tests -v
cd backend && pytest -v
cd ../simulator && pytest -v
cd ../frontend && npm test && npm run typecheck && npm run lint && npm run build
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
```

Then run independent calibration validator against at least one saved real or explicitly labeled test revision.

Validation report status:

```text
Ready to share
Share with caveats
Needs revision
```

- [ ] **Step 1: Run complete regression**
- [ ] **Step 2: Run independent formula recomputation**
- [ ] **Step 3: Record any missing real biomass-reference evidence as a caveat/blocker**
- [ ] **Step 4: Confirm no hidden fallback constants exist in backend/frontend**

## Module 5.5 Exit Criteria

- [ ] Calibration/revision provenance survives active-profile changes.
- [ ] Headline scientific formulas independently recompute within documented tolerances.
- [ ] Invalid inputs remain null with reasons.
- [ ] Extrapolation is visible.
- [ ] Scientific labels avoid permanent-sequestration overclaim.
- [ ] Real calibration evidence limitations are explicit rather than fabricated.
- [ ] Full Phase 0 to 5 regression passes before Phase 6 starts.
