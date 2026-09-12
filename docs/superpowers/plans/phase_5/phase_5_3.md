# Phase 5.3: Experiment Calibration Binding and Processing Integration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind each experiment to one immutable calibration revision, capture an auditable biomass baseline, and make the live/persisted telemetry pipeline use that bound calibration for reproducible scientific derivations.

**Architecture:** Experiment arms gain a calibration binding and baseline record. FastAPI resolves calibration in this order: running experiment bound revision, otherwise active Monitor profile, otherwise no calibration. Historical experiment calculations never consult a mutable global active profile. Processed telemetry gains explicit quality/provenance fields while the raw device schema remains unchanged.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, existing telemetry service, pytest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Raw `device-telemetry.v1` does not change.
- Experiment scientific derivations use only the bound revision.
- Changing active default calibration has no effect on a running or completed experiment.
- Experiment cannot start with a missing/nonexistent selected revision.
- Biomass/carbon are unavailable until a valid baseline is established.
- Baseline includes telemetry sequence and server timestamp for audit.
- A telemetry gap does not fabricate a baseline.
- Reprocessing old raw telemetry with a different revision is an explicit future analysis operation, never silent live behavior.

---

### Task 1: Add experiment calibration and baseline persistence

**Files:**
- Modify: `backend/src/biovolt_backend/experiments/models.py`
- Modify: `backend/src/biovolt_backend/experiments/schemas.py`
- Test: `backend/tests/experiments/test_calibration_binding.py`

Per arm add:

```text
calibration_revision_id nullable FK
baseline_telemetry_sample_id nullable FK
baseline_sequence nullable integer
baseline_timestamp nullable datetime
baseline_biomass_g_l nullable float
baseline_dry_biomass_g nullable float
```

- [ ] **Step 1: Write persistence test for arm binding/baseline**
- [ ] **Step 2: Implement fields and relationships**
- [ ] **Step 3: Ensure completed experiment can still resolve revision after active profile changes**
- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/experiments/test_calibration_binding.py -v
git add src/biovolt_backend/experiments/models.py src/biovolt_backend/experiments/schemas.py tests/experiments/test_calibration_binding.py
git commit -m "feat: bind calibration revisions to BioVolt experiment arms"
```

---

### Task 2: Require valid selected calibration before experiment start

**Files:**
- Modify: `backend/src/biovolt_backend/experiments/service.py`
- Modify: `backend/src/biovolt_backend/experiments/orchestrator.py`
- Test: `backend/tests/experiments/test_calibration_start_gate.py`

Ready/start rules:
- revision exists
- electrical calibration valid for every arm
- if operator requests optical/biomass reporting, corresponding calibration sections are complete
- reactor volume required for reactor biomass/carbon reporting
- start snapshots/reference-locks revision before commands are sent

- [ ] **Step 1: Write missing-revision rejection test**
- [ ] **Step 2: Write invalid electrical calibration rejection test**
- [ ] **Step 3: Write valid revision binding remains stable during start test**
- [ ] **Step 4: Implement validation in service before `ready -> starting`**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/experiments/test_calibration_start_gate.py -v
git add src/biovolt_backend/experiments/service.py src/biovolt_backend/experiments/orchestrator.py tests/experiments/test_calibration_start_gate.py
git commit -m "feat: gate BioVolt experiments on valid calibration"
```

---

### Task 3: Integrate calibrated derivations into telemetry service

**Files:**
- Modify: `backend/src/biovolt_backend/services/telemetry_service.py`
- Modify: `backend/src/biovolt_backend/models/telemetry.py`
- Modify: `backend/src/biovolt_backend/persistence/models.py`
- Test: `backend/tests/services/test_calibrated_telemetry.py`

Processed telemetry additions/clarifications:

```text
corrected_voltage_mv
current_ua
power_uw
od680
biomass_g_l
dry_biomass_g
biomass_delta_g
estimated_co2_biofixed_g
calibration_revision_id
biomass_extrapolated
derivation_quality
experiment_id nullable
```

Rules:
- use bound revision when source belongs to a running experiment arm
- otherwise use active default calibration for Monitor view if one exists
- no profile means calibrated derived values that require it are null
- energy accumulator uses calibrated `power_uw`
- continuity/gap rules from Phase 3.7 remain authoritative

- [ ] **Step 1: Write bound-revision derivation test**
- [ ] **Step 2: Write active-default Monitor test**
- [ ] **Step 3: Write no-calibration null test**
- [ ] **Step 4: Write active-profile change does not affect running experiment test**
- [ ] **Step 5: Implement resolver + derivation integration**
- [ ] **Step 6: Run and commit**

```bash
pytest tests/services/test_calibrated_telemetry.py tests/domain tests/calibration -v
git add src/biovolt_backend/services/telemetry_service.py src/biovolt_backend/models/telemetry.py src/biovolt_backend/persistence/models.py tests/services/test_calibrated_telemetry.py
git commit -m "feat: process BioVolt telemetry with bound calibration"
```

---

### Task 4: Implement automatic experiment baseline capture

**Files:**
- Create: `backend/src/biovolt_backend/experiments/baseline.py`
- Modify: `backend/src/biovolt_backend/services/telemetry_service.py`
- Test: `backend/tests/experiments/test_baseline.py`

**Interfaces:**

```python
class BaselineService:
    async def consider_sample(self, experiment_id: str, arm_id: str, processed: ProcessedTelemetry) -> None: ...
```

Eligibility:
- experiment state is `running`
- arm baseline absent
- sample matches arm device/cell
- biomass and dry biomass are eligible/non-null
- sample not flagged stale or invalid

Capture exactly once using a database compare/update guard so simultaneous frames cannot create two baselines.

- [ ] **Step 1: Write first-eligible-sample capture test**
- [ ] **Step 2: Write invalid first sample then valid second sample test**
- [ ] **Step 3: Write baseline immutability test**
- [ ] **Step 4: Implement transaction-safe one-time capture**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/experiments/test_baseline.py -v
git add src/biovolt_backend/experiments/baseline.py src/biovolt_backend/services/telemetry_service.py tests/experiments/test_baseline.py
git commit -m "feat: capture auditable BioVolt biomass baselines"
```

---

### Task 5: Add explicit manual pre-start baseline capture option

**Files:**
- Modify: `backend/src/biovolt_backend/api/experiments.py`
- Modify: `backend/src/biovolt_backend/experiments/baseline.py`
- Test: `backend/tests/api/test_experiment_baseline.py`

Protected route:

```text
POST /api/experiments/{experiment_id}/arms/{arm_id}/baseline/capture
```

Rules:
- only `ready` experiment
- fresh latest telemetry <= 3 s
- selected bound calibration already set
- biomass eligible
- captures latest sequence/time/mass
- start preserves manually captured baseline instead of replacing it

- [ ] **Step 1: Write ready/fresh capture test**
- [ ] **Step 2: Write stale/unready rejection tests**
- [ ] **Step 3: Implement protected route**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/api/test_experiment_baseline.py -v
git add src/biovolt_backend/api/experiments.py src/biovolt_backend/experiments/baseline.py tests/api/test_experiment_baseline.py
git commit -m "feat: support explicit BioVolt pre-start biomass baseline"
```

---

### Task 6: Preserve calibration provenance in telemetry export/query responses

**Files:**
- Modify: `backend/src/biovolt_backend/api/telemetry.py`
- Modify: `backend/src/biovolt_backend/persistence/telemetry_repository.py`
- Test: `backend/tests/api/test_calibrated_history.py`

- [ ] **Step 1: Add history response test with `calibration_revision_id` and quality flags**
- [ ] **Step 2: Ensure persisted rows retain derived values calculated at observation time**
- [ ] **Step 3: Do not recalculate historical rows using current active profile on normal GET**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/api/test_calibrated_history.py -v
git add src/biovolt_backend/api/telemetry.py src/biovolt_backend/persistence/telemetry_repository.py tests/api/test_calibrated_history.py
git commit -m "feat: preserve BioVolt calibration provenance in telemetry history"
```

## Module 5.3 Exit Criteria

- [ ] Every running arm has a stable calibration revision reference.
- [ ] Monitor default-profile changes cannot alter experiment calculations.
- [ ] Baseline is captured once and auditable by sequence/timestamp.
- [ ] Biomass/carbon remain unavailable until baseline exists.
- [ ] Calibrated power feeds energy accumulation without bypassing telemetry-gap safety.
- [ ] Persisted historical derived values are not silently recomputed under a new profile.
