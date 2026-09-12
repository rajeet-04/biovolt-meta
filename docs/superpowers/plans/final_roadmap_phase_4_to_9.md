# BioVolt Final Implementation Roadmap: Phase 4 to Phase 9

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement each phase task-by-task. Every phase has its own implementation plan and must pass its exit gate before the next phase begins.

**Goal:** Complete BioVolt from the Phase 3 real-hardware boundary through safe experiment control, calibration, adaptive optimization, scientific analytics, production deployment, and final hackathon acceptance.

**Architecture:** The remaining work preserves the approved offline-first split: ESP32 owns physical sensing, actuator safety, and adaptive control; FastAPI owns scientific calculations, experiment orchestration, calibration profiles, persistence, and analytics; the React PWA owns operator workflows and visualization. Each later phase adds one capability layer without weakening the source-neutral telemetry boundary proven in Phases 1 to 3.

**Tech Stack:** ESP32 + PlatformIO + FreeRTOS, FastAPI + SQLite, React + TypeScript + Vite + Tailwind + Recharts + Zustand + Dexie, Docker Compose + Nginx + optional Cloudflared.

**Spec:** `docs/architecture/software-architecture.md`

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
Phase 9 end-to-end scientific, resilience, UX, and demo acceptance
        |
        v
BioVolt release candidate
```

## Phase 4: Experiments, Commands, and Operator Control

**Purpose:** Establish the safe bidirectional control substrate before any adaptive algorithm is allowed to actuate hardware.

Delivers:
- versioned `device-command.v1` and `device-ack.v1` contracts
- experiment lifecycle persistence and state machine
- command IDs, TTLs, acknowledgement, idempotency, and timeout semantics
- ESP32 command parser with safety-gated application
- Passive and Manual modes only
- lightweight operator PIN/session protection
- PWA experiment and control workflows with explicit pending/applied/rejected states

**Hard gate:** Adaptive mode remains unavailable until reliable command delivery, acknowledgement, and experiment state transitions are proven.

## Phase 5: Calibration and Scientific Quantification

**Purpose:** Make every derived scientific claim reproducible from a versioned calibration profile.

Delivers:
- load-resistor and ADS offset calibration fields
- optical dark and blank references
- OD680 calculation tied to a selected profile
- OD680 to dry-biomass calibration points and regression
- reactor volume and experiment baseline biomass
- estimated CO2 biofixed into biomass using an explicit documented conversion assumption
- calibration wizard and profile history
- immutable calibration snapshot binding at experiment start

**Hard gate:** Biomass and carbon values remain null unless the active experiment has a valid calibration profile and baseline.

## Phase 6: Adaptive Control

**Purpose:** Add the actual closed-loop optimization only after sensing, safety, experiments, and calibration are stable.

Delivers:
- host-tested Perturb & Observe state machine
- grow-light PWM as the first optimization actuator
- BPV voltage-squared as the local objective proxy, which is monotonic with power for a fixed positive load resistance
- settling windows, PWM step bounds, direction reversal, hold behavior, manual override, and safe fallback
- mixer remains rule/cooldown controlled, not part of the P&O search space
- Adaptive experiment mode and optimization telemetry/audit

**Hard gate:** No measured gain claim is produced by the control layer itself. Gain is computed later from persisted experiment data.

## Phase 7: Analytics and Scientific Reporting

**Purpose:** Convert completed experiments into defensible comparisons without fabricating statistical certainty.

Primary decision KPI:

```text
matched_window_energy_gain_pct =
  (adaptive_energy_mj - passive_energy_mj)
  / passive_energy_mj * 100
```

The comparison uses a common matched elapsed-time window. If passive energy is non-positive or either arm lacks adequate observed data, the gain is unavailable.

Driver metrics:
- mean and median electrical power
- cumulative energy
- energy per hour
- grow-light PWM duty
- mixer duty
- valid-sample coverage

Scientific outcome metrics:
- OD680 change
- dry biomass concentration change
- reactor dry biomass gain
- estimated CO2 biofixed into biomass

Guardrails:
- temperature excursions
- telemetry gap fraction
- sensor validity coverage
- calibration validity
- matched-window comparability

**Statistical rule:** The hackathon MVP reports descriptive measured differences. It must not display p-values, statistical significance, or confidence intervals unless independent replicate-level methodology is explicitly implemented and validated.

## Phase 8: Production Packaging and Judge Access

**Purpose:** Turn the development stack into a one-command local deployment while keeping public exposure optional and read-only.

Delivers:
- production React build served by Nginx
- same-origin `/api/*`, `/ws/device`, and `/ws/dashboard` proxying
- persistent backend SQLite/CSV volume
- `docker compose up -d` local launch
- two Nginx access surfaces: full local operator and read-only public
- optional Cloudflared profile targeting only the read-only listener
- public route blocks device WebSocket and all state-changing operator/calibration/experiment APIs
- capability endpoint so the PWA can render a clearly read-only judge experience

## Phase 9: Final Acceptance and Demo Readiness

**Purpose:** Validate the whole system as a scientific prototype, not merely as working software.

Delivers:
- independent electrical calculation spot checks
- OD680/calibration sanity checks
- CSV recomputation of headline experiment metrics
- telemetry gap and null-handling verification
- cold-start and offline operation test
- backend/hotspot interruption recovery
- long hardware soak
- operator/public security checks
- final Product Design audit checkpoint for the judge journey
- final Data Analytics validation checkpoint for headline claims
- documented judge demo runbook and clearly labeled simulator fallback procedure

## Product Design Requirements Across Remaining Phases

The implementation plans must preserve these experience rules:
- the default dashboard answers system status before requiring interaction
- operator actions show `pending`, `applied`, `rejected`, or `failed`, never optimistic success without device acknowledgement
- dangerous controls are visually separated from monitoring
- stale/cached/disconnected data is never styled as live
- calibration is a guided wizard with explicit prerequisites and review before activation
- experiment start shows the selected mode, cell/arm, calibration profile, and setpoints before confirmation
- public judge mode is visibly read-only
- simulation fallback, when used, is explicitly labeled synthetic/demo data

Full Product Design visual ideation/audit execution should be performed in a supported Product Design Work surface during the implementation/QA phase; this roadmap records the required product-flow gates.

## Data Analytics Requirements Across Remaining Phases

Every experiment metric must have:
- a precise formula
- unit
- source fields
- aggregation grain
- eligibility rule
- null rule
- comparison window
- quality guardrail where relevant

Headline claims must be blocked when their source data is not trustworthy enough to support them. The final analytics validation must independently recompute the highest-impact values from persisted/exported data before they are used in a judge-facing summary.

## Global Non-Negotiables

- No Raspberry Pi dependency.
- Venue internet is optional.
- Cloudflared is never required for the local demo.
- ESP32 remains safe when laptop/backend/network is unavailable.
- Frontend never independently recalculates FastAPI-owned scientific values.
- Raw ESP32 telemetry never starts carrying FastAPI-derived scientific fields.
- Public exposure never enables actuator or calibration writes.
- Estimated CO2 wording remains `Estimated CO2 biofixed into biomass`.
- No permanent-sequestration claim is made unless permanent biomass storage is actually demonstrated.
- No arbitrary OD-to-biomass constant is used. Conversion requires calibration data.
- No A/B gain is displayed from synthetic or incomplete measurements as if it were observed experimental evidence.

## Final Completion Gate

BioVolt is release-candidate ready only when all six remaining phase exit criteria are met and the Phase 9 acceptance matrix has no unresolved blocker affecting hardware safety, measurement integrity, experiment reproducibility, operator security, or judge-facing claim accuracy.
