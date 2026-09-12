# Phase 9.3: Final Product and Judge-Journey Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the production BioVolt experience is understandable, trustworthy, accessible, and efficient for both operators and judges under real demo conditions.

**Architecture:** Audit the production build, not design mockups. Review the complete judge and operator journeys against evidence provenance, access mode, freshness, scientific terminology, responsive behavior, keyboard accessibility, and failure-state comprehension. Findings are ranked by release severity and fixed in the owning frontend/backend phase.

**Tech Stack:** Production React PWA, browser accessibility tooling/manual checks, responsive viewports, keyboard-only navigation, production read-only and operator modes.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints
- Correctness and provenance take priority over visual polish.
- Public judge mode must never imply control capability.
- Scientific values must include units and unavailable/estimated distinctions.
- Live, stale, offline, cached, synthetic, and measured states must be visually and semantically distinct.
- Accessibility failures blocking navigation or interpretation are MAJOR issues.

---

### Task 1: Judge first-impression audit

**Files:**
- Create: `docs/release/product-audit.md`
- Create: `docs/release/judge-journey.md`

- [ ] Open the public production URL from a fresh browser session.
- [ ] Verify the first viewport explains what BioVolt is, current system state, read-only status, and whether evidence is live/measured/synthetic.
- [ ] Confirm judges can reach Results/experiment comparison within two obvious navigation actions.
- [ ] Confirm no raw engineering jargon is required to interpret headline cards without hiding drill-down detail.
- [ ] Record confusion points and severity before changing copy/layout.
- [ ] Commit `docs: audit BioVolt judge first impression`.

### Task 2: Scientific-copy and trust audit

**Files:**
- Modify: `docs/release/product-audit.md`
- Test: frontend copy regression tests where practical.

- [ ] Search production-visible copy for claims like permanent sequestration, guaranteed optimization, fabricated percentage improvement, or unlabeled simulation.
- [ ] Verify OD680 is described as optical-density-derived, not a direct sensor reading.
- [ ] Verify biomass and CO2 are explicitly estimated/calibration-dependent.
- [ ] Verify adaptive gain is shown only for eligible matched measured experiments.
- [ ] Verify unavailable metrics explain why rather than silently displaying zero.
- [ ] Commit `test: validate BioVolt scientific product copy`.

### Task 3: Operator workflow audit

**Files:**
- Modify: `docs/release/product-audit.md`
- Create: `docs/release/operator-journey.md`

- [ ] Walk through connect -> calibration/profile selection -> create experiment -> start passive/manual/adaptive mode as appropriate -> stop -> Results -> export.
- [ ] Verify destructive/high-impact actions require deliberate confirmation where designed.
- [ ] Verify command pending/ack/failure states are visible and not confused with actual actuator state.
- [ ] Verify manual/adaptive ownership transitions are understandable.
- [ ] Verify operator can recover from backend/device disconnect without refreshing blindly or issuing duplicate control commands.
- [ ] Commit `docs: audit BioVolt operator workflow`.

### Task 4: Responsive and accessibility audit

**Files:**
- Create: `docs/release/accessibility-audit.md`
- Modify frontend tests only if failures are found during implementation.

**Viewports:** desktop laptop, tablet-width, phone-width.

- [ ] Verify no essential KPI/control/status is clipped or horizontally inaccessible.
- [ ] Navigate all primary routes using keyboard only.
- [ ] Verify visible focus, logical tab order, accessible names for controls, and status announcements where state changes matter.
- [ ] Verify charts have textual summaries/labels sufficient for interpretation without relying only on color.
- [ ] Verify read-only/unavailable controls are not represented only by color.
- [ ] Verify reduced-motion preference does not hide state transitions.
- [ ] Classify any core-navigation/accessibility blocker as MAJOR.
- [ ] Commit `docs: complete BioVolt accessibility release audit`.

### Task 5: Failure-state comprehension audit

**Files:**
- Modify: `docs/release/product-audit.md`

- [ ] Observe UI during backend restart, hotspot loss, stale telemetry, cached offline data, sensor failure, invalid calibration, and public read-only mode.
- [ ] For each state, ask whether a judge/operator can tell: what happened, whether data is current, whether control is safe/available, and what action is possible.
- [ ] Verify stale/cached data retains original timestamp and never looks live.
- [ ] Verify synthetic/demo mode remains labeled during disconnect/offline viewing.
- [ ] Commit `test: audit BioVolt failure-state comprehension`.

### Task 6: Product release gate

**Files:**
- Create: `scripts/release/phase9_product_gate.py`
- Create: `docs/release/product-release-checklist.md`

- [ ] Convert audit findings into BLOCKER/MAJOR/MINOR list with owning phase/component.
- [ ] Require zero BLOCKER and zero MAJOR issues.
- [ ] Require judge and operator journeys to complete without undocumented workaround.
- [ ] Capture final production screenshots after fixes for the release evidence pack.
- [ ] Commit `test: add BioVolt product release gate`.

## Exit Criteria
- [ ] Judge view is immediately understandable and visibly read-only.
- [ ] Scientific claims/copy match actual measurement eligibility.
- [ ] Operator workflow is coherent and command state is unambiguous.
- [ ] Responsive and keyboard accessibility gates pass.
- [ ] Failure/offline states explain current data validity clearly.
- [ ] Zero BLOCKER and zero MAJOR product findings remain.
