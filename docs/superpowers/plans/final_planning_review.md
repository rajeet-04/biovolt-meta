# BioVolt Final Planning Review: Superpowers + Ponytail

**Status:** Planning complete through Phase 9. Implementation has not been started by this review.

**Purpose:** Record the final cross-phase self-review before implementation begins. This document is normative where it clarifies cross-phase execution, product-design, evidence, or release-gate expectations without changing the approved architecture.

## Plan Inventory

```text
Phase 0  Repository/contracts
Phase 1  Backend + simulator
Phase 2  Installable PWA
Phase 3  Real ESP32 hardware
Phase 4  Experiments + reliable commands + operator control
Phase 5  Calibration + scientific quantification
Phase 6  Adaptive P&O
Phase 7  Analytics + A/B reporting
Phase 8  Production deployment + read-only judge access
Phase 9  Independent final release validation
```

Remaining-roadmap detail is fully defined through:

```text
phase_4/*
phase_5/*
phase_6/*
phase_7/*
phase_8/phase_8_0.md ... phase_8_4.md
phase_9/phase_9_0.md ... phase_9_4.md
```

Master roadmap:

`docs/superpowers/plans/final_roadmap_phase_4_to_9.md`

---

## Superpowers Cross-Phase Review

### Architecture ownership remains consistent

```text
ESP32
  raw acquisition
  real-time actuator safety
  local mode/control execution
  Adaptive P&O

FastAPI
  protocol validation
  scientific derivations
  experiments/orchestration
  calibration revisions
  persistence
  analytics/reporting

React PWA
  visualization
  operator workflows
  read-only judge experience
  no independent scientific recalculation
```

No later plan is allowed to move current/power/OD680/biomass/CO2 calculations into React or to make browser/backend connectivity a prerequisite for ESP32 safety.

### Simulator substitution remains clean

```text
Simulator -> /ws/device -> FastAPI
```

is replaced by:

```text
ESP32 -> /ws/device -> FastAPI
```

without simulator-specific backend branches. Real hardware timing may jitter; the backend does not assume exact 500 ms arrival intervals.

### Reliable control precedes optimization

Phase ordering deliberately requires:

```text
reliable command/ACK + experiments
        ↓
calibration/science
        ↓
Adaptive P&O
        ↓
A/B analytics
```

Adaptive mode cannot bypass Phase 4 command ownership or Phase 3 firmware safety.

### Tests and gates precede claims

Each phase defines acceptance before downstream capabilities rely on it. Phase 9 independently recomputes the highest-impact scientific and A/B values rather than trusting production calculations by self-comparison.

### No-moving-goalposts rule

Final release thresholds are frozen before Phase 9 execution. Failure is fixed at its source instead of weakening a gate after results are known.

---

## Ponytail Cross-Phase Product Review

Ponytail product-design requirements are normative across Phase 4-9 even where older module files say generic `Product Design`.

### Core product principle: state truth before visual confidence

A user must be able to distinguish:

```text
live
stale
backend disconnected
device disconnected
cached/offline
unavailable
measured
simulation/demo
operator
public read-only
pending command
ACK/applied command
rejected/failed command
```

No styling or animation may make stale/cached/synthetic evidence appear more current or measured than it is.

### Judge journey

```text
Open read-only view
-> understand system + evidence state
-> inspect live status
-> open Results
-> understand primary comparison/eligibility
-> inspect supporting evidence
-> export safe data
```

Results should be reachable with one obvious navigation action from Overview in the production judge experience.

### Operator journey

```text
Open local view
-> authenticate if required
-> inspect readiness/calibration
-> create/select experiment
-> start mode deliberately
-> observe command pending/ACK/rejection
-> operate/monitor safely
-> stop
-> review/export Results
```

No optimistic UI may imply a hardware command executed before device acknowledgement/telemetry confirms it.

### Recovery journey

```text
Failure
-> truthful degraded state
-> stale/unsafe actions unavailable
-> useful recovery guidance
-> actual system recovery
-> fresh evidence arrives
-> UI returns to Live
```

Recovery banners clear only after real healthy evidence, not merely because a retry timer fired.

---

## Scientific Claim Review

Locked wording/semantics:

```text
OD680
Estimated Biomass
Estimated CO2 biofixed into biomass
Light (lux)
Simulation / demo data
Unavailable
```

Guardrails:
- OD680 is derived from optical transmission, not a direct sensor measurement.
- BPW34 health means acquisition succeeded, not that calibration is valid.
- Biomass requires calibrated OD-to-dry-biomass regression.
- Carbon requires eligible biomass delta/baseline/volume/provenance.
- No permanent-sequestration claim without actual permanent biomass storage evidence.
- BH1750 is lux, not PAR.
- P&O is not marketed as machine learning.
- Ineligible A/B comparison is `Unavailable`, not `0%`.
- Negative measured gain is valid and remains visible.
- Synthetic evidence cannot satisfy a measured-gain claim.

---

## Security and Offline Review

### Local first

Core operation remains independent of upstream internet:

```text
ESP32 <-> laptop hotspot/LAN <-> Nginx/FastAPI/PWA
```

Cloudflared is optional and targets only the read-only Nginx listener.

### Public read-only

Public surface cannot:
- access `/ws/device`
- log in as operator
- create/start/stop/update experiments
- issue actuator commands
- write/activate calibration
- elevate access by browser-supplied headers

Frontend capability hiding is presentation only; Nginx and FastAPI enforce security.

### Offline writes

Service worker never queues/replays control, auth, experiment, or calibration mutations.

---

## Data Integrity Review

### Energy continuity

Energy integration uses observed device uptime intervals and does not bridge known sequence gaps/network outages.

### Calibration provenance

Experiments bind to immutable calibration revisions so historical analytics remain reproducible after later calibration updates.

### Final analytics

Primary comparison:

```text
matched_window_energy_gain_pct =
  (adaptive_energy_mj - passive_energy_mj)
  / passive_energy_mj * 100
```

Only eligible matched measured evidence can produce the judge-facing measured gain.

### Final independent release validation

Phase 9 requires three-way consistency:

```text
independent recomputation
       ↕
production API
       ↕
production PWA
```

Headline disagreement beyond frozen tolerance is BLOCKER.

---

## Final Resilience Thresholds

Planned release thresholds include:

```text
mandatory production services healthy <= 90 s
ESP32 + fresh telemetry after restored path <= 30 s
healthy-network telemetry silence failure > 10 s
final real-hardware soak >= 60 min
unexpected ESP32 reboot = 0
actuator safety violations = 0
stale command replay = 0
data corruption/loss = 0
```

The 60-minute release soak is stronger than earlier development/HIL smoke tests and is deliberately reserved for Phase 9.

---

## Self-Review Corrections Already Applied

- Corrected Phase 8.2 backend paths from inconsistent `backend/app/...` to the established `backend/src/biovolt_backend/...` structure.
- Made public access fail closed and independent of frontend hiding.
- Added explicit Ponytail judge-entry and recovery-state matrices to Phase 8.
- Added explicit scientific copy/unit audit to Phase 9.1.
- Added real-failure visible-state audit and fixed resilience thresholds to Phase 9.2.
- Converted Phase 9.3 into the final Ponytail product/judge/operator/accessibility audit.
- Added independent claim traceability, truthful fallback ladder, and offline demo narrative to Phase 9.4.
- Updated the master roadmap so Ponytail requirements are normative across all Phase 4-9 modules.
- Repository search found no unresolved planning hit for the combined `TODO/TBD/backend/app` review query after corrections; implementation should still treat any later discovered stale path as a plan defect to correct before coding that task.

---

## Implementation Start Rule

Planning is now complete. Implementation should begin at the earliest unimplemented prerequisite phase and proceed serially:

```text
Phase 0 gate
-> Phase 1 gate
-> Phase 2 gate
-> Phase 3 gate
-> Phase 4 gate
-> Phase 5 gate
-> Phase 6 gate
-> Phase 7 gate
-> Phase 8 gate
-> Phase 9 release gate
```

If Phases 0-3 have not actually been implemented yet, do not jump directly to Phase 4 merely because Phase 4-9 planning is complete.

## Final Planning Decision

**APPROVED FOR IMPLEMENTATION PLANNING EXECUTION.**

No additional feature-planning phase is required after Phase 9. New functionality discovered during implementation should be evaluated against scope and either:
- fixed inside the owning phase when required for correctness/safety, or
- recorded as post-hackathon/stretch work when it is not required for the release-candidate gate.
