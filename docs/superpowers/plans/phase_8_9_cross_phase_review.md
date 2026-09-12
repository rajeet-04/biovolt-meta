# BioVolt Phase 8-9 Cross-Phase Superpowers Review

**Purpose:** Final planning-only review before implementation begins.

## Review Scope

Reviewed:
- `docs/superpowers/plans/phase_8/phase_8_0.md`
- `phase_8_1.md`
- `phase_8_2.md`
- `phase_8_3.md`
- `phase_8_4.md`
- `docs/superpowers/plans/phase_9/phase_9_0.md`
- `phase_9_1.md`
- `phase_9_2.md`
- `phase_9_3.md`
- `phase_9_4.md`
- `docs/superpowers/plans/final_roadmap_phase_4_to_9.md`

## Superpowers Self-Review Results

### 1. Spec Coverage

All remaining roadmap responsibilities have an owning plan:

```text
production packaging/security     -> Phase 8.1, 8.2
production/offline product UX     -> Phase 8.3
deployment resilience/operations  -> Phase 8.4
scientific independent validation -> Phase 9.1
hardware/resilience HIL           -> Phase 9.2
product/judge audit               -> Phase 9.3
independent analytics/release     -> Phase 9.4
```

No additional product-development phase is planned after Phase 9. A failure in Phase 9 is routed back to the phase that owns the defect.

### 2. Source Ownership Consistency

Frozen ownership remains consistent:

```text
ESP32
  raw sensing
  actuator safety
  real-time control
  P&O adaptive optimization

FastAPI
  current/power derivation
  OD680/biomass/carbon derivation
  calibration revisions
  experiments
  persistence
  comparison analytics

React PWA
  presentation
  operator/judge workflows
  no independent scientific recomputation

Independent release scripts
  validation only
  must not be imported by production code
```

### 3. Simulator / Real Hardware Boundary

The deterministic simulator remains replaceable:

```text
simulator -> /ws/device -> FastAPI
ESP32     -> /ws/device -> FastAPI
```

No Phase 8 or 9 plan adds simulator-specific backend behavior. Experiment provenance, not raw device schema, carries `measured` versus `synthetic_demo` evidence classification.

### 4. Scientific Claim Rules

Frozen rules:
- current and power use calibrated load resistance
- OD680 requires dark and blank optical calibration
- biomass requires OD-to-dry-biomass calibration
- CO2 is `Estimated CO2 biofixed into biomass`
- no permanent sequestration/removal claim
- synthetic/demo experiments cannot satisfy a measured-performance claim
- invalid/incomplete metrics are `Unavailable`, never silently `0`
- negative measured adaptive gain is preserved honestly

### 5. Data Freshness Rules

Phase 8.3 now freezes:

```text
LIVE: latest valid telemetry age <= 2 s
STALE: >2 s and <=6 s with backend reachable
DEVICE DISCONNECTED: >6 s or backend device state disconnected while backend reachable
BACKEND DISCONNECTED: backend/dashboard transport unavailable
CACHED OFFLINE: explicit timestamped local cache presentation
```

A reconnect returns to `live` only after a genuinely newer telemetry frame arrives.

### 6. Resilience Thresholds

Phase 9.2 now freezes:
- production mandatory services healthy <= 60 s
- ESP32 Wi-Fi <= 30 s after power-on
- authenticated device WebSocket <= 60 s after power-on
- first valid persisted telemetry <= 75 s
- PWA live <= 90 s
- backend/hotspot recovery to fresh device telemetry <= 30 s after path restoration
- final release soak >= 60 continuous minutes

### 7. Analytics Validation Tolerances

Phase 9.4 now freezes:

```text
comparison duration: exact after API normalization
energy: <= max(0.001 mJ, 0.1% relative)
gain: <= 0.05 percentage points
coverage/duty fractions: <= 0.001 absolute
eligibility/evidence/quality/reason codes: exact
```

The independent validator cannot import production analytics modules.

### 8. Public Security Boundary

Public mode remains structurally read-only:
- Cloudflared targets read-only Nginx only
- `/ws/device` is blocked publicly
- operator auth writes blocked
- experiment/control/calibration writes blocked
- Nginx allow-list plus FastAPI defense-in-depth
- client-supplied access-mode headers cannot elevate privileges

### 9. Product Design / Ponytail Planning Rules

Product-planning requirements are frozen into the executable plans:
- judge first sees system state, evidence provenance, and read-only state
- scientific eligibility precedes headline claims
- operator command UI differentiates pending/applied/rejected/failed
- stale/offline/synthetic states are explicit and not color-only
- `Light (lux)` is used for BH1750, not PAR
- public mode contains no misleading enabled controls
- final audit is performed on the production build, not mockups

## Placeholder Scan

Remaining plans intentionally contain no `TBD`, `TODO`, `implement later`, or unspecified acceptance placeholders in the Phase 8-9 critical gates. Event-specific official judge slot length is the only externally variable value; the plan defaults the core demonstration to <=5 minutes unless official event rules require another duration.

## Phase Execution Order

```text
Implement and verify Phase 4
        ↓
Phase 5
        ↓
Phase 6
        ↓
Phase 7
        ↓
Phase 8
        ↓
Phase 9 release validation
        ↓
Release candidate
```

No implementation should skip directly to later phases merely because simulator or UI work appears demo-ready.

## Planning Freeze Decision

**Status: READY FOR IMPLEMENTATION AFTER THE EARLIER PHASE DEPENDENCIES ARE MERGED.**

The roadmap is fully planned through the final release gate. New features discovered during implementation should be treated as scope changes and explicitly assigned to a phase rather than silently inserted into the release acceptance phase.
