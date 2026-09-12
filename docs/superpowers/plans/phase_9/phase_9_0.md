# Phase 9 Overview: Final Release-Candidate Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task-by-task. Apply Ponytail product-design reasoning to every production screen, journey, state transition, and judge-facing claim audited in this phase. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the completed BioVolt system as a release candidate across scientific integrity, hardware safety, resilience, product usability, accessibility, analytics correctness, public security, and judge-demo readiness.

**Architecture:** Phase 9 adds no new core product capability unless a blocking defect is discovered. It independently verifies the system built in Phases 0-8 using acceptance scripts, physical HIL procedures, analytics recomputation, production UI review, adversarial public-access tests, and a timed demo rehearsal. Any failed gate returns work to the owning earlier phase instead of weakening acceptance criteria.

**Tech Stack:** Existing BioVolt stack, pytest/Vitest/PlatformIO, Docker Compose, independent Python validation scripts, browser production PWA, physical ESP32/BPV hardware.

**Spec:** `docs/superpowers/plans/final_roadmap_phase_4_to_9.md`

## Global Constraints

- Phase 9 is validation/release hardening, not feature expansion.
- Measured and synthetic evidence remain distinguishable.
- Scientific claims require valid calibration, provenance, data quality, and measured evidence where specified.
- Public access remains read-only.
- Local operation remains independent of internet/Cloudflared.
- Hardware safety overrides demo convenience.
- A failed gate is fixed at its source; thresholds are not relaxed after results are known.
- No `Unavailable` scientific metric is converted to zero merely to simplify presentation.
- Final screenshots and demo flow must reflect the real production build, not design mocks.
- Release candidate requires zero BLOCKER and zero MAJOR issues.

---

## Module Map

### 9.1 Scientific, Electrical, and Calibration Validation
Plan: `docs/superpowers/plans/phase_9/phase_9_1.md`

Produces:
- independent electrical/current/power recomputation
- energy continuity validation
- independent OD680 validation
- biomass/CO2 eligibility validation
- physical bench sanity checks
- scientific claim/copy integrity gate

### 9.2 Cold-Start, Failure, Safety, and Soak Validation
Plan: `docs/superpowers/plans/phase_9/phase_9_2.md`

Produces:
- clean cold-start proof
- backend/Nginx/device/hotspot/internet failure drills
- actuator safety HIL verification
- long-running hardware soak
- persistence/recovery evidence
- no-regression resilience report

### 9.3 Final Ponytail Product and Judge-Journey Audit
Plan: `docs/superpowers/plans/phase_9/phase_9_3.md`

Produces:
- production screenshot audit
- judge/operator/recovery journey audit
- information hierarchy review
- responsive/accessibility review
- terminology/copy consistency review
- final presentation mode readiness

### 9.4 Final Analytics, Demo, and Release Gate
Plan: `docs/superpowers/plans/phase_9/phase_9_4.md`

Produces:
- independent headline analytics recomputation
- A/B comparison eligibility verification
- release evidence pack
- timed offline demo runbook/rehearsal
- final severity review
- release-candidate decision

---

## Release Evidence Pack

Create outside source-controlled secrets:

```text
release-evidence/
├── system-info.txt
├── git-revision.txt
├── firmware-version.txt
├── calibration-revisions.json
├── cold-start-report.json
├── resilience-report.json
├── soak-report.json
├── hardware-safety-report.json
├── scientific-validation.json
├── analytics-recompute.json
├── public-security-report.json
├── accessibility-report.md
├── product-audit.md
├── screenshots/
│   ├── judge-desktop/
│   ├── judge-mobile/
│   ├── operator/
│   └── failure-states/
├── demo-rehearsal.md
└── release-checklist.md
```

Only non-sensitive evidence is committed if useful. Never include:
- device token
- Wi-Fi credentials
- operator PIN/PIN hash
- Cloudflare tunnel credential
- private `.env`

---

## Severity Rules

### BLOCKER

```text
unsafe actuator behavior
scientific formula/provenance/eligibility error
public write exposure or public /ws/device exposure
data corruption or loss
inability to run core system locally without internet
synthetic evidence presented as measured
headline analytics disagreement beyond tolerance
```

### MAJOR

```text
broken experiment/calibration/adaptive/results flow
stale/cached data shown as live
unreliable reconnect/recovery
judge cannot understand evidence provenance or comparison eligibility
critical accessibility failure blocking keyboard/use
operator cannot identify safe recovery action
```

### MINOR

```text
cosmetic/non-blocking issue that does not affect correctness, safety,
accessibility, provenance, recovery, or demo comprehension
```

Release candidate requires:

```text
BLOCKER = 0
MAJOR   = 0
```

MINOR issues may remain only when documented and demonstrably irrelevant to safety/correctness/demo comprehension.

---

## No-Moving-Goalposts Rule

Before Phase 9 execution begins, freeze:
- formula tolerances
- soak duration/minimum evidence cadence
- acceptable telemetry freshness thresholds
- public route classification
- accessibility checklist
- judge demo sequence
- analytics eligibility rules
- severity definitions

If a threshold must change because the original plan is technically wrong, document the rationale in the owning earlier phase and review it before rerunning acceptance.

---

## Planned Commit Sequence

1. `test: add BioVolt scientific release validation`
2. `test: add BioVolt resilience and safety release validation`
3. `test: add Ponytail BioVolt final product experience audit`
4. `test: add BioVolt release-candidate gate`

## Phase 9 Exit Criteria

- [ ] Electrical calculations independently agree with source measurements/calibration.
- [ ] OD680, biomass, and CO2 claims are eligible only with valid provenance.
- [ ] Hardware actuator safety is demonstrated physically.
- [ ] Cold start, backend restart, hotspot loss, internet loss, and full-stack restart recover as designed.
- [ ] Hardware soak passes without unexpected reboot, runaway actuator, progressive heap collapse, corrupt persistence, or silent telemetry death.
- [ ] Public surface cannot write or reach device WebSocket.
- [ ] Production PWA clearly communicates live/stale/offline/read-only/synthetic/unavailable states.
- [ ] Ponytail product audit finds no MAJOR hierarchy, journey, copy, or accessibility defect.
- [ ] Independent analytics recomputation agrees with production headline results within frozen tolerance.
- [ ] Demo can be executed from documented runbook without upstream internet.
- [ ] Release evidence pack is complete and contains no secrets.
- [ ] Release candidate has zero BLOCKER and zero MAJOR findings.
