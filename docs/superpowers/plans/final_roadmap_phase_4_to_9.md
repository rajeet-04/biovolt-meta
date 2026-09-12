# BioVolt Final Implementation Roadmap: Phase 4 to Phase 9

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement each phase task-by-task. Apply Ponytail product-design reasoning across all Phase 4-9 user journeys, product states, information hierarchy, control affordances, scientific copy, and judge-facing evidence. Every phase has its own implementation plan and must pass its exit gate before the next phase begins.

**Goal:** Complete BioVolt from the Phase 3 real-hardware boundary through safe experiment control, calibration, adaptive optimization, scientific analytics, production deployment, and final hackathon release-candidate acceptance.

**Architecture:** The remaining work preserves the approved offline-first split: ESP32 owns physical sensing, actuator safety, and adaptive control; FastAPI owns scientific calculations, experiment orchestration, calibration profiles, persistence, and analytics; the React PWA owns operator workflows and visualization. Each phase adds one capability layer without weakening the source-neutral telemetry boundary proven in Phases 1-3.

**Tech Stack:** ESP32 + PlatformIO + FreeRTOS, FastAPI + SQLite, React + TypeScript + Vite + Tailwind + Recharts + Zustand + Dexie, Docker Compose + Nginx + optional Cloudflared.

**Spec:** `docs/architecture/software-architecture.md`

---

## Final Phase Sequence

```text
Phase 3 real hardware parity
        |
        v
Phase 4 experiment lifecycle + reliable command/ack + operator controls
        |
        v
Phase 5 calibration profiles + scientific quantification chain
        |
        v
Phase 6 adaptive Perturb & Observe control
        |
        v
Phase 7 experiment analytics + A/B comparison + scientific reporting
        |
        v
Phase 8 production packaging + read-only public judge access
        |
        v
Phase 9 independent scientific/resilience/product/analytics/demo acceptance
        |
        v
BioVolt release candidate
```

No later phase may be implemented before the preceding phase's mandatory gate passes, except isolated preparatory work that does not depend on unverified behavior and is explicitly approved.

---

# Superpowers Execution Discipline Across All Remaining Phases

Every module follows:

```text
read approved module plan
-> write/confirm failing tests or acceptance expectations first
-> implement smallest coherent slice
-> run targeted verification
-> run regression subset
-> review against module scope and architecture ownership
-> commit logical checkpoint
-> pass module exit criteria
-> continue
```

Rules:
- do not implement from memory when a module plan exists
- do not redefine Phase 0 contracts inside later components
- do not move scientific calculations into the frontend
- do not move safety ownership from ESP32 into browser/backend convenience code
- do not hide test failures by weakening acceptance thresholds
- implementation findings may update plans only when the architecture assumption is demonstrably wrong; document the reason before continuing
- one phase branch/PR is preferred for each phase, with logical commits matching module boundaries

Recommended branches:

```text
phase/04-experiments-control
phase/05-calibration-science
phase/06-adaptive-control
phase/07-analytics-reporting
phase/08-production-deployment
phase/09-release-validation
```

---

# Ponytail Product-Design Contract Across Phase 4-9

These requirements are normative even where an older phase module file uses generic `Product Design` wording.

## State truth before polish

Every important value/action must answer:

```text
Is it live, stale, cached, unavailable, measured, or synthetic?
Who owns the current control state?
Has a command merely been sent, or actually acknowledged/applied?
Is a scientific result eligible to claim?
```

The UI never substitutes visual confidence for missing evidence.

## Primary journeys

**Judge:**
```text
open read-only view
-> understand system/evidence state
-> inspect live status
-> open completed Results
-> understand primary comparison and eligibility
-> inspect supporting evidence/export
```

**Operator:**
```text
open local view
-> authenticate when required
-> inspect readiness/calibration
-> create/start experiment
-> observe acknowledged control state
-> stop experiment
-> review/export Results
```

**Recovery:**
```text
failure occurs
-> UI identifies truthful degraded state
-> unsafe/stale actions are unavailable
-> operator sees useful recovery action
-> system recovers
-> UI returns to healthy only after real fresh evidence
```

## Scientific copy contract

Required concepts:
- `OD680`
- `Estimated Biomass`
- `Estimated CO2 biofixed into biomass`
- `Light (lux)` for BH1750
- `Simulation / demo data`
- `Unavailable` with reason where known

Forbidden unless implementation truly changes:
- permanent carbon sequestration/removal claims
- `PAR` for BH1750
- P&O presented as ML prediction
- synthetic gain presented as measured gain
- ineligible comparison represented as `0%`

## Action hierarchy

- monitoring is visually separate from mutation/control
- dangerous or high-impact actions are deliberate
- pending/ACK/rejected command state is explicit
- public mode has no enabled-looking operator controls
- cached/offline state never queues control writes

---

# Phase 4: Experiments, Commands, and Operator Control

**Purpose:** Establish the safe bidirectional control substrate before any adaptive algorithm actuates hardware.

Delivers:
- versioned `device-command.v1` and `device-ack.v1`
- experiment lifecycle persistence/state machine
- command IDs, TTLs, acknowledgement, idempotency, timeout semantics
- ESP32 safety-gated command parser
- Passive and Manual modes
- lightweight operator PIN/session protection
- PWA experiment/control workflows with pending/applied/rejected states

Ponytail gate:
- command state cannot be confused with physical actuator state
- operator understands experiment mode/calibration/setpoints before start
- public/judge experience remains observation-only when later exposed

**Hard gate:** Adaptive mode remains unavailable until reliable delivery, acknowledgement, ownership, and experiment state transitions are proven.

---

# Phase 5: Calibration and Scientific Quantification

**Purpose:** Make every derived scientific claim reproducible from a versioned calibration revision.

Delivers:
- load resistor and ADS offset calibration
- optical dark/blank references
- calibrated OD680
- OD680 to dry-biomass calibration points/regression
- reactor volume and experiment baseline
- estimated CO2 biofixed into biomass
- calibration wizard/history
- immutable calibration revision bound to experiment

Ponytail gate:
- wizard prerequisites and progress are clear
- calibration quality/eligibility is visible before activation
- historical experiment provenance remains inspectable
- unavailable science is explained rather than filled with placeholders

**Hard gate:** Biomass/carbon remain unavailable unless all required calibration/baseline/provenance inputs pass eligibility.

---

# Phase 6: Adaptive Control

**Purpose:** Add closed-loop optimization only after sensing, safety, experiments, and calibration are stable.

Delivers:
- host-tested Perturb & Observe state machine
- grow-light PWM as first optimization actuator
- BPV voltage-squared local objective proxy for fixed positive load resistance
- settling windows, PWM bounds, direction reversal, hold, manual preemption, safe fallback
- mixer remains rule/cooldown controlled outside the P&O search variable
- Adaptive experiment mode and optimization audit events

Ponytail gate:
- Adaptive ownership is unmistakable
- operator can see optimizer decision state without implying guaranteed improvement
- Manual/Stop preemption is explicit
- safety overrides are understandable and never hidden

**Hard gate:** Control layer never generates a measured-gain claim. Gain comes from Phase 7 persisted experiment analytics.

---

# Phase 7: Analytics and Scientific Reporting

**Purpose:** Convert completed experiments into defensible comparisons without fabricating certainty.

Primary decision KPI:

```text
matched_window_energy_gain_pct =
  (adaptive_energy_mj - passive_energy_mj)
  / passive_energy_mj * 100
```

Comparison uses a common matched elapsed-time window and observed intervals only.

Driver metrics:
- mean/median electrical power
- cumulative energy
- energy per hour
- grow-light PWM duty
- mixer duty
- valid-sample coverage

Scientific outcomes:
- OD680 change
- dry biomass concentration change
- reactor dry biomass gain
- estimated CO2 biofixed into biomass

Guardrails:
- temperature excursions
- telemetry gap fraction
- sensor validity coverage
- calibration validity
- evidence class
- matched-window comparability

Ponytail gate:
- headline result has supporting provenance and quality context
- negative measured gain is shown honestly
- ineligible comparison becomes `Unavailable` with reason
- synthetic/demo evidence is unmistakable

**Statistical rule:** Hackathon MVP reports descriptive measured differences. No p-values/significance/confidence intervals without validated replicate-level methodology.

---

# Phase 8: Production Packaging and Judge Access

**Purpose:** Turn development stack into one-command local production deployment while keeping public exposure optional/read-only.

Modules:

```text
8.1 production frontend/Nginx/Compose
8.2 fail-closed public boundary + optional Cloudflared
8.3 production access-mode/offline/evidence UX
8.4 deployment resilience/security/operations acceptance
```

Delivers:
- static production React build served by Nginx
- same-origin `/api/*`, `/ws/device`, `/ws/dashboard` local proxy
- persistent backend SQLite/CSV volume
- `docker compose up -d` local launch
- separate operator and public-read-only Nginx listeners
- optional Cloudflared targeting read-only listener only
- capabilities endpoint
- public penetration matrix
- production journey/recovery/accessibility contracts

Ponytail gate:
- judge URL is immediately understandable and read-only
- live/stale/cached/simulation states remain explicit
- public tunnel failure is not confused with local-system failure
- no hidden security dependency on frontend-only control removal

---

# Phase 9: Final Release-Candidate Acceptance

**Purpose:** Validate the entire system as a scientific prototype and demo product, not merely working software.

Modules:

```text
9.1 independent scientific/electrical/calibration/claim validation
9.2 cold-start/failure/hardware-safety/60-minute soak validation
9.3 final Ponytail product/judge/operator/accessibility audit
9.4 independent analytics/demo/release-candidate gate
```

Delivers:
- independent scientific recomputation
- physical bench checks
- immutable calibration provenance verification
- clean cold-start and failure recovery evidence
- actuator safety HIL
- 60-minute real-hardware soak
- public security recheck
- Ponytail production screenshot/journey audit
- independent A/B analytics recomputation
- claim traceability table
- offline demo narrative/fallback ladder/rehearsal
- release evidence pack
- binary PASS/FAIL release gate

Final release requires:

```text
Phase 9.1 PASS
Phase 9.2 PASS
Phase 9.3 PASS
Phase 9.4 PASS
BLOCKER = 0
MAJOR = 0
```

---

# Data Analytics Contract Across Remaining Phases

Every experiment metric has:
- exact formula
- unit
- source fields
- aggregation grain
- eligibility rule
- null rule
- comparison window
- quality guardrail
- evidence/provenance requirement where relevant

Headline claims are blocked when source evidence cannot support them. The final release gate independently recomputes the highest-impact values from persisted/exported evidence.

---

# Global Non-Negotiables

- No Raspberry Pi dependency.
- Venue/upstream internet is optional.
- Cloudflared is never required locally.
- ESP32 remains safe when laptop/backend/network is unavailable.
- Frontend never independently recalculates FastAPI-owned scientific values.
- Raw ESP32 telemetry never starts carrying FastAPI-derived scientific fields.
- Public exposure never enables actuator/calibration/experiment/auth writes.
- Estimated CO2 wording remains `Estimated CO2 biofixed into biomass`.
- No permanent-sequestration claim without actual permanent biomass storage evidence.
- No arbitrary OD-to-biomass constant; conversion requires calibration.
- No A/B gain from synthetic/incomplete evidence is presented as observed measurement.
- Failed/stale/cached states never masquerade as live.
- No stale control command is replayed after reconnect.

---

# Planning Completion Status

The implementation roadmap is fully specified through the final phase:

```text
Phase 4 planned
Phase 5 planned
Phase 6 planned
Phase 7 planned
Phase 8.1-8.4 planned
Phase 9.1-9.4 planned
```

The next action after final planning self-review is **implementation**, beginning from the earliest unimplemented prerequisite phase and proceeding serially through each mandatory gate.

# Final Completion Gate

BioVolt is release-candidate ready only when all Phase 4-9 exit criteria have been implemented and the Phase 9 acceptance matrix reports zero unresolved BLOCKER/MAJOR findings affecting hardware safety, measurement integrity, experiment reproducibility, operator/public security, accessibility, recovery truthfulness, or judge-facing claim accuracy.
