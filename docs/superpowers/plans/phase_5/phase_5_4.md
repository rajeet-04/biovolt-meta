# Phase 5.4: PWA Calibration Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a guided operator-only calibration workflow that captures trustworthy live measurements, collects known biomass reference points, exposes fit diagnostics, and activates a reviewed immutable calibration revision.

**Architecture:** The wizard is a staged React workflow backed entirely by Phase 5 calibration APIs. Raw values are captured server-side from fresh telemetry. Draft form state may live in Zustand during the session, but scientific coefficients and fit metrics always come back from FastAPI. The wizard never writes directly to ESP32 NVS because Phase 5 calibration is backend scientific metadata, not device sensor firmware calibration.

**Tech Stack:** React, TypeScript, React Router, Zustand, Recharts, existing backend API client patterns, Vitest, React Testing Library.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Route requires operator session for create/revise/activate actions.
- Read-only profile history may remain visible when logged out.
- Wizard does not accept fabricated sensor raw values for dark/blank capture.
- Capture button is disabled for stale/disconnected/unhealthy source.
- Known dry biomass values are operator-entered laboratory/reference values and must be explicitly labeled as such.
- Fit coefficients are read-only backend results.
- Wizard does not claim fit quality is universally good based on R² alone.
- Profile activation requires a final review step.
- Leaving the wizard before save does not partially mutate an existing revision.

---

### Task 1: Add calibration routes, types, and store

**Files:**
- Create: `frontend/src/types/calibration.ts`
- Create: `frontend/src/lib/calibrationApi.ts`
- Create: `frontend/src/stores/calibrationWizardStore.ts`
- Create: `frontend/src/pages/CalibrationPage.tsx`
- Create: `frontend/src/pages/CalibrationWizardPage.tsx`
- Modify: `frontend/src/app/router.tsx`
- Test: `frontend/tests/calibration/calibrationWizardStore.test.ts`

Routes:

```text
/calibration
/calibration/new
/calibration/:profileId/revise
/calibration/:profileId
```

Wizard draft state:

```text
source device/cell
profile name/notes
load resistance
ADC offset
dark capture
blank capture
biomass reference points
reactor volume
CO2 biomass factor
optional offsets
```

- [ ] **Step 1: Write initial/reset draft-store tests**
- [ ] **Step 2: Implement API types matching backend response**
- [ ] **Step 3: Add profile-list/detail routes**
- [ ] **Step 4: Add guarded create/revise wizard routes**
- [ ] **Step 5: Run and commit**

```bash
cd frontend
npm test -- calibrationWizardStore
npm run typecheck
git add src/types/calibration.ts src/lib/calibrationApi.ts src/stores/calibrationWizardStore.ts src/pages/CalibrationPage.tsx src/pages/CalibrationWizardPage.tsx src/app/router.tsx tests/calibration/calibrationWizardStore.test.ts
git commit -m "feat: scaffold BioVolt calibration wizard"
```

---

### Task 2: Implement prerequisites and electrical calibration step

**Files:**
- Create: `frontend/src/components/calibration/CalibrationStepper.tsx`
- Create: `frontend/src/components/calibration/PrerequisitesStep.tsx`
- Create: `frontend/src/components/calibration/ElectricalStep.tsx`
- Test: `frontend/tests/calibration/ElectricalStep.test.tsx`

Prerequisite panel shows:

```text
device connected
telemetry freshness
ADS1115 health
BPW34 path health
temperature/light health for context
```

Electrical step:
- precision load resistor in ohms
- optional measured ADS zero/offset entry from actual zero-reference procedure
- live BPV raw/mV capture preview

- [ ] **Step 1: Write stale device prevents capture/continue test**
- [ ] **Step 2: Write non-positive resistor validation test**
- [ ] **Step 3: Implement source/freshness status using existing telemetry store**
- [ ] **Step 4: Keep displayed measurement timestamp/sequence beside captured values**
- [ ] **Step 5: Run and commit**

```bash
npm test -- ElectricalStep
npm run typecheck
git add src/components/calibration/CalibrationStepper.tsx src/components/calibration/PrerequisitesStep.tsx src/components/calibration/ElectricalStep.tsx tests/calibration/ElectricalStep.test.tsx
git commit -m "feat: add BioVolt calibration prerequisites and electrical step"
```

---

### Task 3: Implement optical dark and blank capture steps

**Files:**
- Create: `frontend/src/components/calibration/OpticalDarkStep.tsx`
- Create: `frontend/src/components/calibration/OpticalBlankStep.tsx`
- Create: `frontend/tests/calibration/OpticalCapture.test.tsx`

Copy requirements:
- dark step explains the physical setup expected by the approved procedure
- blank step explicitly says use blank medium/reference condition, not live algae sample
- both capture through `/api/calibration/capture/optical`
- show captured raw value, sequence, time, source

- [ ] **Step 1: Write capture-response rendering tests**
- [ ] **Step 2: Write stale/health error rendering test**
- [ ] **Step 3: Block progression when blank <= dark**
- [ ] **Step 4: Implement recapture button that replaces draft capture only, not saved revision**
- [ ] **Step 5: Run and commit**

```bash
npm test -- OpticalCapture
npm run typecheck
git add src/components/calibration/OpticalDarkStep.tsx src/components/calibration/OpticalBlankStep.tsx tests/calibration/OpticalCapture.test.tsx
git commit -m "feat: capture BioVolt optical dark and blank references"
```

---

### Task 4: Implement biomass calibration-point entry and fit review

**Files:**
- Create: `frontend/src/components/calibration/BiomassPointsStep.tsx`
- Create: `frontend/src/components/calibration/FitReviewStep.tsx`
- Create: `frontend/src/components/calibration/BiomassFitChart.tsx`
- Test: `frontend/tests/calibration/BiomassPointsStep.test.tsx`
- Test: `frontend/tests/calibration/FitReviewStep.test.tsx`

Workflow:

```text
capture/current eligible OD680 or enter reviewed OD value from calibration measurement
enter known dry biomass concentration g/L for that sample
add point
repeat >=3 distinct OD values
submit draft to backend preview-fit endpoint or revision-create validation path
review slope/intercept/R²/RMSE/range
```

If a preview endpoint is needed, add in implementation only as:

```text
POST /api/calibration/preview-fit
```

operator protected, non-persistent, using the exact backend fit function.

Chart rules:
- x = OD680
- y = dry biomass g/L
- points + fitted line
- axes/unit labels
- no truncated/deceptive scales without clear reason

- [ ] **Step 1: Write >=3 distinct OD validation tests**
- [ ] **Step 2: Write negative biomass rejection test**
- [ ] **Step 3: Implement point table with remove/edit before save**
- [ ] **Step 4: Implement fit-review metrics directly from backend**
- [ ] **Step 5: Add visible calibration OD range**
- [ ] **Step 6: Run and commit**

```bash
npm test -- BiomassPointsStep FitReviewStep
npm run typecheck
git add src/components/calibration/BiomassPointsStep.tsx src/components/calibration/FitReviewStep.tsx src/components/calibration/BiomassFitChart.tsx tests/calibration
git commit -m "feat: review BioVolt OD biomass calibration fit"
```

---

### Task 5: Implement reactor/scientific metadata and final review

**Files:**
- Create: `frontend/src/components/calibration/ReactorMetadataStep.tsx`
- Create: `frontend/src/components/calibration/CalibrationReviewStep.tsx`
- Test: `frontend/tests/calibration/CalibrationReviewStep.test.tsx`

Review displays exact provenance:

```text
profile/revision target
source device/cell used for live captures
load resistance
ADC offset
dark/blank raw values and capture times
biomass points
fit diagnostics
reactor volume
CO2 per dry biomass factor and source notes
optional offsets
```

Activation is separate from save:

```text
Save revision -> revision exists but not active
Activate -> explicit second action
```

- [ ] **Step 1: Write final-review completeness test**
- [ ] **Step 2: Write save does not auto-activate test**
- [ ] **Step 3: Write activate confirmation test**
- [ ] **Step 4: Implement source-note field for CO2 factor/reference assumption**
- [ ] **Step 5: Run and commit**

```bash
npm test -- CalibrationReviewStep
npm run typecheck
git add src/components/calibration/ReactorMetadataStep.tsx src/components/calibration/CalibrationReviewStep.tsx tests/calibration/CalibrationReviewStep.test.tsx
git commit -m "feat: review and activate BioVolt calibration revision"
```

---

### Task 6: Integrate calibration selection into experiment setup

**Files:**
- Modify: `frontend/src/components/experiments/ExperimentForm.tsx`
- Modify: `frontend/src/pages/ExperimentDetailPage.tsx`
- Test: `frontend/tests/experiments/ExperimentCalibration.test.tsx`

- [ ] **Step 1: Show active calibration revision by default but require explicit selection/confirmation**
- [ ] **Step 2: Show revision number and key fit diagnostics/range in selector details**
- [ ] **Step 3: Disable Ready when required calibration section is invalid**
- [ ] **Step 4: Show bound revision on running/completed experiment as immutable provenance**
- [ ] **Step 5: Run and commit**

```bash
npm test -- ExperimentCalibration
npm run typecheck
npm run lint
git add src/components/experiments/ExperimentForm.tsx src/pages/ExperimentDetailPage.tsx tests/experiments/ExperimentCalibration.test.tsx
git commit -m "feat: select immutable calibration for BioVolt experiments"
```

## Module 5.4 Exit Criteria

- [ ] Wizard is staged and prerequisite-driven rather than one dense form.
- [ ] Raw optical references come from fresh backend capture.
- [ ] Fit diagnostics are server-owned and visibly presented.
- [ ] No arbitrary `good fit` R² threshold is presented as scientific truth.
- [ ] Save and Activate are separate intentional actions.
- [ ] Running/completed experiment shows its immutable calibration revision.
- [ ] Wizard never writes scientific calibration directly to ESP32 NVS.
