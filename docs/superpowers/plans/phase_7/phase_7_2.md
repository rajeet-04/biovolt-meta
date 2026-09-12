# Phase 7.2: Experiment Analytics Service, API, and Export Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build bounded, reproducible analytics queries that load persisted experiment telemetry, apply Phase 7.1 domain calculations, expose summary/comparison/series APIs, and export provenance-rich CSV.

**Architecture:** `AnalyticsRepository` performs bounded SQL queries by experiment arm/time. `AnalyticsService` maps ORM rows to pure analytics inputs, invokes domain functions, and assembles API views. Long-series aggregation occurs server-side. CSV export contains raw persisted experiment rows plus repeated provenance columns so independent recomputation does not require hidden application state.

**Tech Stack:** FastAPI, SQLAlchemy async, SQLite, Pydantic v2, Python `csv`, pytest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Analytics endpoints are read-only.
- Queries are bounded by experiment and explicit/default row limits.
- Headline metrics are computed from persisted rows, not current in-memory dashboard state.
- Existing historical persisted values are not silently recalibrated with current active profile.
- Series aggregation does not interpolate missing buckets.
- CSV uses machine-readable unrounded values where practical.
- API response includes analytics configuration provenance such as coverage threshold and gap threshold.

---

### Task 1: Add analytics repository for experiment arms

**Files:**
- Create: `backend/src/biovolt_backend/analytics/repository.py`
- Create: `backend/tests/analytics/test_repository.py`

**Interfaces:**

```python
class AnalyticsRepository:
    async def arm_samples(
        self,
        experiment_id: str,
        arm_id: str,
        *,
        started_at: datetime,
        ended_at: datetime | None,
        limit: int = 200_000,
    ) -> list[TelemetrySample]: ...
```

Rules:
- filter by arm device/cell and experiment time window
- order ascending by received_at/id
- reject unreasonable limit above configured maximum
- no unbounded full telemetry-table scan

- [ ] **Step 1: Write correct arm/time filtering test**
- [ ] **Step 2: Write chronological ordering test**
- [ ] **Step 3: Write hard limit validation test**
- [ ] **Step 4: Implement repository with indexed query path**
- [ ] **Step 5: Run and commit**

```bash
cd backend
pytest tests/analytics/test_repository.py -v
git add src/biovolt_backend/analytics/repository.py tests/analytics/test_repository.py
git commit -m "feat: query BioVolt experiment telemetry for analytics"
```

---

### Task 2: Implement experiment analytics service

**Files:**
- Create: `backend/src/biovolt_backend/analytics/service.py`
- Create: `backend/src/biovolt_backend/analytics/schemas.py`
- Create: `backend/tests/analytics/test_service.py`

**Interfaces:**

```python
class AnalyticsService:
    async def summary(self, experiment_id: str) -> ExperimentAnalyticsSummary: ...
    async def comparison(self, experiment_id: str, passive_arm_id: str, adaptive_arm_id: str) -> ComparisonView: ...
    async def series(self, experiment_id: str, bucket_s: int) -> ExperimentSeriesView: ...
```

Summary includes for each arm:
- identity/mode/label
- calibration revision
- evidence class
- full observed duration
- electrical/control/scientific metrics
- quality metrics

Experiment-level response includes available Passive/Adaptive comparison candidates but does not guess which arms to compare when more than one of either exists.

- [ ] **Step 1: Write two-arm summary test**
- [ ] **Step 2: Write explicit comparison test**
- [ ] **Step 3: Write missing experiment/arm errors**
- [ ] **Step 4: Implement mapping to Phase 7.1 pure domain functions**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/analytics/test_service.py -v
git add src/biovolt_backend/analytics/service.py src/biovolt_backend/analytics/schemas.py tests/analytics/test_service.py
git commit -m "feat: assemble BioVolt experiment analytics summaries"
```

---

### Task 3: Implement bucketed time-series aggregation

**Files:**
- Create: `backend/src/biovolt_backend/analytics/series.py`
- Create: `backend/tests/analytics/test_series.py`

Allowed `bucket_s` initially:

```text
1, 5, 10, 30, 60
```

Per bucket/arm response:

```text
elapsed_start_s
sample_count
power_mean_uw
power_min_uw
power_max_uw
voltage_mean_mv
od680_mean
biomass_mean_g_l
temperature_mean_c
grow_led_pwm_mean
mixer_on_fraction
```

Missing source bucket -> no point for that bucket.

- [ ] **Step 1: Write exact 5-second bucket fixture test**
- [ ] **Step 2: Write null metric exclusion test**
- [ ] **Step 3: Write missing bucket remains absent test**
- [ ] **Step 4: Implement deterministic elapsed bucket assignment**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/analytics/test_series.py -v
git add src/biovolt_backend/analytics/series.py tests/analytics/test_series.py
git commit -m "feat: aggregate BioVolt experiment chart series"
```

---

### Task 4: Add analytics REST endpoints

**Files:**
- Create: `backend/src/biovolt_backend/api/analytics.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Create: `backend/tests/api/test_analytics.py`

Routes:

```text
GET /api/experiments/{id}/analytics/summary
GET /api/experiments/{id}/analytics/series?bucket_s=5
GET /api/experiments/{id}/analytics/comparison?passive_arm_id=...&adaptive_arm_id=...
```

Response rules:
- comparison returns HTTP 200 even when metric ineligible; body contains `eligible=false`, null gain, reasons
- malformed/wrong arm IDs use appropriate validation/not-found errors
- synthetic evidence is explicit in response

- [ ] **Step 1: Write summary/comparison/series API tests**
- [ ] **Step 2: Write ineligible comparison response test**
- [ ] **Step 3: Implement router**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/api/test_analytics.py -v
git add src/biovolt_backend/api/analytics.py src/biovolt_backend/main.py tests/api/test_analytics.py
git commit -m "feat: expose BioVolt experiment analytics API"
```

---

### Task 5: Add provenance-rich CSV export

**Files:**
- Create: `backend/src/biovolt_backend/analytics/export.py`
- Modify: `backend/src/biovolt_backend/api/analytics.py`
- Create: `backend/tests/analytics/test_export.py`

Route:

```text
GET /api/experiments/{id}/analytics/export.csv
```

Every row includes:

```text
experiment_id
experiment_name
evidence_class
experiment_started_at
experiment_ended_at
arm_id
arm_label
mode
device_id
cell_id
calibration_revision_id
baseline_sequence
baseline_timestamp
received_at
sequence
uptime_ms
bpv_voltage_mv
corrected_voltage_mv
current_ua
power_uw
cumulative_energy_mj
od680
biomass_g_l
dry_biomass_g
biomass_delta_g
estimated_co2_biofixed_g
temperature_c
lux
grow_led_pwm
mixer_on
biomass_extrapolated
```

Use blank CSV cell for null, not numeric zero.

- [ ] **Step 1: Write header/provenance test**
- [ ] **Step 2: Write null -> blank cell test**
- [ ] **Step 3: Write multiple-arm row test**
- [ ] **Step 4: Stream/write export without loading arbitrary global history**
- [ ] **Step 5: Commit**

```bash
pytest tests/analytics/test_export.py -v
git add src/biovolt_backend/analytics/export.py src/biovolt_backend/api/analytics.py tests/analytics/test_export.py
git commit -m "feat: export BioVolt experiment analytics with provenance"
```

---

### Task 6: Add analytics configuration provenance

**Files:**
- Modify: `backend/src/biovolt_backend/config.py`
- Modify: `backend/src/biovolt_backend/analytics/schemas.py`
- Modify: `backend/tests/analytics/test_service.py`

Include in summary/comparison:

```text
minimum_power_coverage_fraction
analytics_gap_threshold_s
nominal_persistence_interval_s
comparison_method = matched_elapsed_window
energy_method = cumulative_difference_single_boot
```

- [ ] **Step 1: Write response provenance test**
- [ ] **Step 2: Validate settings ranges**
- [ ] **Step 3: Implement response inclusion**
- [ ] **Step 4: Run all analytics tests and commit**

```bash
pytest tests/analytics tests/api/test_analytics.py -v
git add src/biovolt_backend/config.py src/biovolt_backend/analytics/schemas.py tests/analytics/test_service.py
git commit -m "feat: disclose BioVolt analytics quality configuration"
```

## Module 7.2 Exit Criteria

- [ ] Analytics queries are experiment-scoped and bounded.
- [ ] Summary/comparison use persisted data and pure KPI domain functions.
- [ ] Missing buckets are not interpolated.
- [ ] Ineligible comparisons return structured null/reasons, not HTTP failure or zero.
- [ ] CSV contains enough provenance for independent recomputation.
- [ ] Analytics quality settings/method are visible in API responses.
