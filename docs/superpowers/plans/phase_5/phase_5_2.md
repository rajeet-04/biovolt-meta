# Phase 5.2: Calibration Persistence, Revisioning, and API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist BioVolt calibration profiles as immutable revisions, expose operator-protected create/revise/activate APIs, and provide safe raw-value capture endpoints for the PWA wizard.

**Architecture:** A stable profile identity groups immutable revisions. The backend owns validation and fitting. The PWA submits raw calibration inputs/known biomass points, but fitted coefficients and quality diagnostics are generated server-side. Capture endpoints read the latest valid backend telemetry for a selected device/cell rather than accepting fabricated raw sensor values from the browser.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.x async ORM, SQLite, existing operator-session dependency, pytest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Calibration revisions are immutable after creation.
- A revision cannot be deleted while referenced by any experiment.
- Editing creates `revision_number + 1` under the same profile ID.
- Only one revision may be the default active revision at a time.
- Activation does not modify historical experiments.
- Backend calculates linear fit coefficients from submitted calibration points.
- PWA cannot submit precomputed R²/RMSE as authoritative values.
- Raw capture requires fresh telemetry, default freshness <= 3 seconds.
- Capture returns timestamp, device/cell, sequence, raw value, and sensor-health context.
- Calibration writes and activation require operator session.

---

### Task 1: Add calibration profile/revision ORM models

**Files:**
- Create: `backend/src/biovolt_backend/calibration/models.py`
- Create: `backend/src/biovolt_backend/calibration/__init__.py`
- Modify: `backend/src/biovolt_backend/persistence/database.py`
- Test: `backend/tests/calibration/test_models.py`

**Profile columns:**

```text
id UUID text primary key
name text
description nullable text
created_at datetime
active_revision_id nullable FK
```

**Revision columns:**

```text
id UUID text primary key
profile_id FK
revision_number integer
created_at datetime
source_notes nullable text
load_resistance_ohm float
ads1115_offset_mv float
optical_dark_raw float nullable
optical_blank_raw float nullable
biomass_model_type text nullable
biomass_slope float nullable
biomass_intercept float nullable
biomass_point_count integer nullable
biomass_r_squared float nullable
biomass_rmse_g_l float nullable
biomass_od_min float nullable
biomass_od_max float nullable
reactor_volume_l float nullable
co2_per_dry_biomass_g_per_g float nullable
temperature_offset_c float nullable
lux_offset float nullable
raw_calibration_points_json text nullable
validation_json text
```

Constraints:
- unique `(profile_id, revision_number)`
- no update path for scientific revision fields after insert

- [ ] **Step 1: Write table and uniqueness tests**
- [ ] **Step 2: Implement models and relationships**
- [ ] **Step 3: Add revision round-trip test preserving raw calibration points**
- [ ] **Step 4: Run and commit**

```bash
cd backend
pytest tests/calibration/test_models.py -v
git add src/biovolt_backend/calibration/models.py src/biovolt_backend/persistence/database.py tests/calibration/test_models.py
git commit -m "feat: persist immutable BioVolt calibration revisions"
```

---

### Task 2: Implement calibration repository and revision service

**Files:**
- Create: `backend/src/biovolt_backend/calibration/repository.py`
- Create: `backend/src/biovolt_backend/calibration/schemas.py`
- Create: `backend/src/biovolt_backend/calibration/service.py`
- Test: `backend/tests/calibration/test_service.py`

**Interfaces:**

```python
class CalibrationService:
    async def create_profile(self, request: CalibrationRevisionCreate) -> CalibrationRevisionView: ...
    async def revise(self, profile_id: str, request: CalibrationRevisionCreate) -> CalibrationRevisionView: ...
    async def activate(self, revision_id: str) -> CalibrationRevisionView: ...
    async def get_profile(self, profile_id: str) -> CalibrationProfileView: ...
    async def get_revision(self, revision_id: str) -> CalibrationRevisionView: ...
    async def list_profiles(self) -> list[CalibrationProfileView]: ...
```

Request carries raw calibration point pairs, not fitted coefficients:

```json
{
  "name": "Chlorella batch 2026-08",
  "load_resistance_ohm": 1000.0,
  "ads1115_offset_mv": 0.7,
  "optical_dark_raw": 120.0,
  "optical_blank_raw": 18400.0,
  "biomass_points": [
    {"od680": 0.15, "dry_biomass_g_l": 0.08},
    {"od680": 0.45, "dry_biomass_g_l": 0.26},
    {"od680": 0.82, "dry_biomass_g_l": 0.48}
  ],
  "reactor_volume_l": 0.5,
  "co2_per_dry_biomass_g_per_g": 1.83
}
```

- [ ] **Step 1: Write create-profile test verifying server-generated fit fields**
- [ ] **Step 2: Write revise creates new revision without mutating revision 1 test**
- [ ] **Step 3: Write activation changes profile pointer only test**
- [ ] **Step 4: Write incomplete optical/biomass profile validation-state test**
- [ ] **Step 5: Implement service using Phase 5.1 pure functions**
- [ ] **Step 6: Run and commit**

```bash
pytest tests/calibration/test_service.py -v
git add src/biovolt_backend/calibration/repository.py src/biovolt_backend/calibration/schemas.py src/biovolt_backend/calibration/service.py tests/calibration/test_service.py
git commit -m "feat: create and revise BioVolt calibration profiles"
```

---

### Task 3: Add raw telemetry capture service

**Files:**
- Create: `backend/src/biovolt_backend/calibration/capture.py`
- Test: `backend/tests/calibration/test_capture.py`

**Interfaces:**

```python
class CalibrationCaptureService:
    async def capture_optical(self, device_id: str, cell_id: str, now: datetime) -> CalibrationCapture: ...
    async def capture_electrical(self, device_id: str, cell_id: str, now: datetime) -> CalibrationCapture: ...
```

Capture response:

```text
device_id
cell_id
sequence
server_timestamp
age_ms
sensor_health
bpv_voltage_mv nullable
bpv_adc_raw nullable
bpw34_raw nullable
bpw34_voltage_mv nullable
```

Rules:
- source is backend latest processed/raw-audit state, not arbitrary request body
- reject stale source > 3 s
- reject missing/false required sensor health
- do not transform raw optical capture into OD here

- [ ] **Step 1: Write fresh optical capture test**
- [ ] **Step 2: Write stale telemetry rejection test**
- [ ] **Step 3: Write sensor-health rejection test**
- [ ] **Step 4: Implement service**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/calibration/test_capture.py -v
git add src/biovolt_backend/calibration/capture.py tests/calibration/test_capture.py
git commit -m "feat: capture BioVolt calibration measurements from live telemetry"
```

---

### Task 4: Add calibration REST API

**Files:**
- Create: `backend/src/biovolt_backend/api/calibration.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Test: `backend/tests/api/test_calibration.py`

**Read routes:**

```text
GET /api/calibration/profiles
GET /api/calibration/profiles/{profile_id}
GET /api/calibration/revisions/{revision_id}
GET /api/calibration/active
```

**Protected writes:**

```text
POST /api/calibration/profiles
POST /api/calibration/profiles/{profile_id}/revisions
POST /api/calibration/revisions/{revision_id}/activate
POST /api/calibration/capture/electrical
POST /api/calibration/capture/optical
```

Capture request contains only device/cell selector.

- [ ] **Step 1: Write unauthenticated write rejection tests**
- [ ] **Step 2: Write create/revise/activate API tests**
- [ ] **Step 3: Write fresh/stale capture API tests**
- [ ] **Step 4: Implement router and response schemas**
- [ ] **Step 5: Run and commit**

```bash
pytest tests/api/test_calibration.py -v
git add src/biovolt_backend/api/calibration.py src/biovolt_backend/main.py tests/api/test_calibration.py
git commit -m "feat: expose BioVolt calibration API"
```

---

### Task 5: Add revision deletion/reference protection policy

**Files:**
- Modify: `backend/src/biovolt_backend/calibration/service.py`
- Create: `backend/tests/calibration/test_revision_protection.py`

Phase 5 preferred policy is no destructive deletion endpoint at all. If repository cleanup is later required, only completely unreferenced profiles may be archived, never hard-deleted measurements.

- [ ] **Step 1: Add test confirming no public DELETE route exists**
- [ ] **Step 2: Add service guard preventing mutation of existing revision scientific fields**
- [ ] **Step 3: Add test that experiment-referenced revision remains readable indefinitely**
- [ ] **Step 4: Run calibration suite and commit**

```bash
pytest tests/calibration tests/api/test_calibration.py -v
git add src/biovolt_backend/calibration/service.py tests/calibration/test_revision_protection.py
git commit -m "test: protect BioVolt calibration revision history"
```

## Module 5.2 Exit Criteria

- [ ] Profile revisions are immutable.
- [ ] Fit coefficients/diagnostics are server-generated.
- [ ] Raw calibration points remain auditable.
- [ ] Active revision is a pointer, not a mutation of old profiles.
- [ ] Capture endpoints use fresh backend telemetry rather than frontend-entered raw values.
- [ ] Calibration writes require operator session.
- [ ] Historical revisions cannot be destructively removed through public API.
