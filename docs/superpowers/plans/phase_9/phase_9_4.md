# Phase 9.4: Final Analytics, Demo, and Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify BioVolt's judge-facing analytics, rehearse the complete offline demo, and produce the final release-candidate decision with explicit evidence.

**Architecture:** A standalone validator recomputes headline A/B metrics from persisted/exported experiment data and compares them to production API/UI outputs. The team then performs a timed demo rehearsal using only the documented production runbook. Release status is granted only if scientific, resilience, product, analytics, and security gates all pass.

**Tech Stack:** Independent Python analytics scripts, CSV/SQLite exports, production API/PWA, Docker Compose, physical BioVolt hardware.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints
- Production analytics must not be trusted by self-comparison alone.
- A/B improvement is shown only when comparison eligibility is satisfied.
- Negative measured gain is a valid result and must not be hidden.
- Synthetic/demo data cannot satisfy a measured-performance release claim.
- The final demo must remain executable without upstream internet.

---

### Task 1: Independent experiment-comparison recomputation

**Files:**
- Create: `scripts/release/recompute_experiment_comparison.py`
- Create: `tests/release/test_recompute_experiment_comparison.py`

- [ ] Read experiment CSV/exported rows without importing production analytics modules.
- [ ] Independently determine the common elapsed comparison window for Passive and Adaptive experiments.
- [ ] Independently integrate eligible energy over that common window while respecting telemetry gaps/reboots.
- [ ] Compute `gain_pct = (adaptive_energy_mj - passive_energy_mj) / passive_energy_mj * 100` only when passive energy is positive and all Phase 7 quality gates are satisfied.
- [ ] Return structured ineligibility reasons instead of substituting `0%`.
- [ ] Add tests for positive gain, negative gain, zero denominator, inadequate coverage, reboot, and synthetic evidence.
- [ ] Commit `test: independently recompute BioVolt experiment comparisons`.

### Task 2: Compare independent analytics with production outputs

**Files:**
- Create: `scripts/release/validate_production_analytics.py`
- Create: `release-evidence/analytics-recompute.example.json` documentation schema only.

- [ ] Fetch production analytics API output for selected release experiments.
- [ ] Recompute from export/raw evidence independently.
- [ ] Compare passive energy, adaptive energy, comparison duration, coverage/quality flags, and gain percentage within documented numeric tolerances.
- [ ] Verify production UI headline matches API and independent result.
- [ ] Verify any ineligible comparison appears as unavailable with the same core reason category.
- [ ] Classify disagreement affecting headline judging as BLOCKER.
- [ ] Commit `test: validate BioVolt production analytics independently`.

### Task 3: Build final offline demo runbook

**Files:**
- Create: `docs/release/demo-runbook.md`
- Create: `docs/release/demo-recovery-cards.md`

**Target demo flow:**
```text
1. Start production stack
2. Show live device connection and raw/derived telemetry
3. Explain BPV voltage -> current/power ownership
4. Show OD680/biomass only if calibration is valid
5. Start or present Passive experiment evidence
6. Start or present Adaptive experiment evidence
7. Show P&O decision trace and firmware safety ownership
8. Open Results comparison with quality/provenance
9. Export CSV / show independent evidence
10. Demonstrate internet independence
```

- [ ] Write exact operator actions and expected visible checkpoints for each step.
- [ ] Add fallback path when wet hardware response is slow: use previously measured experiment history, clearly labeled as measured historical data, not simulated live data.
- [ ] Add separate fallback path for unavailable hardware using simulation, with explicit `Simulation / demo data` labeling and no measured-gain claim.
- [ ] Add recovery cards for backend restart, ESP32 reconnect, hotspot issue, stale dashboard, and Cloudflared failure.
- [ ] Commit `docs: add BioVolt final demo runbook`.

### Task 4: Timed judge rehearsal

**Files:**
- Create: `docs/release/demo-rehearsal.md`

- [ ] Run the demo from a fresh production start using the runbook, with upstream internet disabled for the primary rehearsal.
- [ ] Time startup-to-ready and each demo section.
- [ ] Require no undocumented shell/source edits during the rehearsal.
- [ ] Have a teammate follow the runbook who did not author the current implementation step, and record ambiguous instructions.
- [ ] Verify every headline number can be traced to an experiment/calibration/provenance screen or export.
- [ ] Repeat until the runbook is executable without improvising critical recovery steps.
- [ ] Commit `docs: record BioVolt final demo rehearsal`.

### Task 5: Final release checklist and evidence aggregation

**Files:**
- Create: `scripts/release/phase9_release_gate.py`
- Create: `docs/release/release-checklist.md`

- [ ] Require Phase 9.1 scientific gate PASS.
- [ ] Require Phase 9.2 resilience gate PASS.
- [ ] Require Phase 9.3 product gate PASS.
- [ ] Require Phase 8 public-security acceptance PASS.
- [ ] Require independent analytics comparison PASS.
- [ ] Require production backend/frontend/firmware/contract test suites PASS.
- [ ] Verify secrets are absent from release evidence and git-tracked files.
- [ ] Emit final machine-readable release status: `PASS` or `FAIL`, with every failed gate listed.
- [ ] Commit `test: add BioVolt final release-candidate gate`.

### Task 6: Release-candidate freeze

**Files:**
- Modify: `README.md`
- Create: `docs/release/release-candidate.md`

- [ ] Record firmware/backend/frontend schema versions used in the accepted build.
- [ ] Record exact production startup command and required environment preparation.
- [ ] Record known MINOR limitations that do not invalidate safety/science/demo correctness.
- [ ] Do not mark release candidate if any BLOCKER or MAJOR issue remains.
- [ ] Tagging/version publication is performed only after the gate reports PASS and the team reviews the evidence.
- [ ] Commit `docs: freeze BioVolt release-candidate configuration`.

## Exit Criteria
- [ ] Independent A/B analytics match production outputs within tolerance.
- [ ] Ineligible/negative/synthetic comparisons are represented honestly.
- [ ] Offline demo runbook is complete and rehearsed.
- [ ] Every headline claim is traceable to evidence/provenance.
- [ ] All scientific, resilience, product, security, and regression gates pass.
- [ ] Zero BLOCKER and zero MAJOR issues remain.
- [ ] BioVolt is ready to be frozen as a release candidate.
