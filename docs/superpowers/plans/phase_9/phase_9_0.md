# Phase 9 Overview: Final Release-Candidate Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate the completed BioVolt system as a release candidate across scientific integrity, hardware safety, resilience, product usability, analytics correctness, and judge-demo readiness.

**Architecture:** Phase 9 adds no new core product capability unless a blocking defect is discovered. It independently verifies the system built in Phases 0-8 using acceptance scripts, physical HIL procedures, analytics recomputation, production UI review, and a timed demo rehearsal. Any failed gate returns work to the owning earlier phase rather than weakening acceptance criteria.

**Tech Stack:** Existing BioVolt stack, pytest/Vitest/PlatformIO, Docker Compose, independent Python analytics scripts, browser-based production PWA, physical ESP32/BPV hardware.

**Spec:** `docs/superpowers/plans/final_roadmap_phase_4_to_9.md`

## Global Constraints
- Phase 9 is validation and release hardening, not a feature-expansion phase.
- Measured and synthetic evidence must remain distinguishable.
- Scientific claims require valid calibration/provenance and measured data.
- Public access must remain read-only.
- Local operation must remain independent of internet/Cloudflared.
- Hardware safety always overrides demo convenience.
- A failed gate is documented and fixed at its source; acceptance thresholds are not relaxed after seeing results.

---

## Module Map

### 9.1 Scientific, Electrical, and Calibration Validation
Plan: `docs/superpowers/plans/phase_9/phase_9_1.md`

### 9.2 Cold-Start, Failure, and Soak Validation
Plan: `docs/superpowers/plans/phase_9/phase_9_2.md`

### 9.3 Final Product and Judge-Journey Audit
Plan: `docs/superpowers/plans/phase_9/phase_9_3.md`

### 9.4 Final Analytics, Demo, and Release Gate
Plan: `docs/superpowers/plans/phase_9/phase_9_4.md`

---

## Release Evidence Pack

Final acceptance must produce an evidence folder outside source-controlled secrets containing:

```text
release-evidence/
├── system-info.txt
├── firmware-version.txt
├── cold-start-report.json
├── soak-report.json
├── scientific-validation.json
├── analytics-recompute.json
├── public-security-report.json
├── screenshots/
├── demo-rehearsal.md
└── release-checklist.md
```

Only non-sensitive evidence should be committed if useful; device tokens, Wi-Fi credentials, operator PINs, and private tunnel credentials are never included.

## Severity Rules

```text
BLOCKER
  unsafe actuator behavior
  scientific calculation/provenance error
  public write exposure
  data corruption/loss
  inability to run locally without internet

MAJOR
  broken core experiment/calibration/adaptive/results flow
  stale data shown as live
  unreliable reconnect/recovery
  judge cannot understand provenance or comparison

MINOR
  cosmetic issue that does not affect correctness, safety, accessibility, or demo comprehension
```

Release candidate requires zero BLOCKER and zero MAJOR issues.

## Planned Commit Sequence
1. `test: add BioVolt scientific release validation`
2. `test: add BioVolt resilience release validation`
3. `test: add BioVolt final product experience audit`
4. `test: add BioVolt release-candidate gate`

## Phase 9 Exit Criteria
- [ ] Electrical calculations independently agree with source measurements/calibration.
- [ ] OD680, biomass, and CO2 claims are eligible only with valid provenance.
- [ ] Hardware safety is demonstrated physically.
- [ ] Cold start, backend restart, hotspot loss, internet loss, and full-stack restart recover as designed.
- [ ] Minimum hardware soak passes without reboot, runaway actuator, progressive heap loss, or corrupt persistence.
- [ ] Public surface cannot perform writes or reach device WebSocket.
- [ ] Production PWA clearly communicates live/stale/offline/read-only/synthetic states.
- [ ] Independent analytics recomputation agrees with production headline results within defined numeric tolerance.
- [ ] Demo can be executed from a documented runbook without internet.
- [ ] Release candidate has zero BLOCKER and zero MAJOR findings.
