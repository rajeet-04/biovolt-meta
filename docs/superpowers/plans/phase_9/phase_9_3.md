# Phase 9.3: Final Ponytail Product and Judge-Journey Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task-by-task. Use Ponytail as the primary product-design lens for hierarchy, comprehension, accessibility, state truthfulness, and demo flow. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify the production BioVolt experience is understandable, trustworthy, accessible, efficient, and presentation-ready for both operators and judges under real demo conditions.

**Architecture:** Audit the actual production build, never design mockups. Review complete judge/operator/recovery journeys against evidence provenance, access mode, freshness, scientific terminology, responsive behavior, keyboard accessibility, information hierarchy, action safety, and failure-state comprehension. Findings are severity-ranked and fixed in the owning earlier phase.

**Tech Stack:** Production React PWA, browser accessibility tooling/manual checks, responsive viewports, keyboard-only navigation, production public/operator modes, release screenshots.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints

- Correctness and provenance outrank visual polish.
- Public judge mode never implies control capability.
- Scientific values include correct units and estimated/unavailable distinctions.
- Live, stale, offline, cached, synthetic, measured, and unavailable states are semantically distinct.
- Accessibility failure blocking core navigation/interpretation is MAJOR.
- Final audit uses production data/evidence or explicitly labeled simulation.
- A prettier screen does not pass if the information hierarchy is misleading.
- No screenshot may hide a warning/provenance state merely to make the demo look cleaner.

---

## Ponytail Audit Heuristics

For every primary screen ask:

```text
1. What is the user's primary question here?
2. What is the single most important answer/state?
3. What evidence proves that answer?
4. What can the user safely do next?
5. What would make the current answer invalid/stale/ineligible?
6. Can a first-time judge understand this without team narration?
```

Primary user groups:
- judge/public viewer
- operator/team member
- teammate recovering from a failure under time pressure

---

### Task 1: Judge first-impression and five-second audit

**Files:**
- Create: `docs/release/product-audit.md`
- Create: `docs/release/judge-journey.md`
- Evidence: `release-evidence/screenshots/judge-desktop/`

Open the public production URL from a fresh browser session.

Within the first viewport a judge should be able to determine:

```text
BioVolt is a real bio-photovoltaic monitoring/control experiment
current system/device status
read-only status
whether displayed evidence is measured or simulation/demo
one or two headline scientific/electrical outcomes
where to open experiment Results
```

- [ ] Capture first viewport before any scrolling.
- [ ] Verify `Read-only judge view` is visible but not the dominant scientific headline.
- [ ] Verify live/stale/offline state is immediately legible.
- [ ] Verify evidence class is visible.
- [ ] Verify Results is reachable in <=1 obvious navigation action from Overview.
- [ ] Ask a teammate unfamiliar with current layout to explain the screen without coaching; record confusion points.
- [ ] Classify inability to distinguish measured vs synthetic or live vs stale as MAJOR/BLOCKER according to impact.
- [ ] Commit `docs: audit BioVolt judge first impression`.

---

### Task 2: Information hierarchy and visual-density audit

**Files:**
- Modify: `docs/release/product-audit.md`
- Create: `docs/release/information-hierarchy-audit.md`

Audit Overview, Live Data, Experiments, Controls, Calibration, Results.

Desired judge-facing priority:

```text
system/evidence state
-> primary experiment outcome
-> supporting electrical/biological KPIs
-> quality/provenance
-> supporting charts/history/export
```

Desired operator priority adds:

```text
active experiment/mode
-> device/command health
-> safe available actions
-> command ACK/rejection
```

- [ ] Remove/flag duplicate KPIs that compete without adding meaning.
- [ ] Confirm units are adjacent to values and not buried in tooltips only.
- [ ] Confirm chart legends/axes do not require domain guessing.
- [ ] Verify no decorative animation competes with warnings or measurement changes.
- [ ] Verify responsive layouts preserve priority instead of merely stacking every card.
- [ ] Commit `docs: audit BioVolt information hierarchy`.

---

### Task 3: Scientific-copy and trust audit

**Files:**
- Modify: `docs/release/product-audit.md`
- Test: frontend copy regression tests where practical

Audit visible copy against Phase 9.1 claim contract.

- [ ] Verify OD680 is not presented as a direct sensor measurement.
- [ ] Verify biomass and CO2 are explicitly estimated/calibration-dependent.
- [ ] Verify CO2 wording is `Estimated CO2 biofixed into biomass`.
- [ ] Verify gain appears only for eligible matched evidence.
- [ ] Verify negative measured gain remains visible as a valid result.
- [ ] Verify ineligible metric is `Unavailable` with reason, never fake `0%`.
- [ ] Verify simulation/demo labels persist on Overview, Results, history, and cached views.
- [ ] Verify `Light (lux)` is used unless actual PAR hardware is added.
- [ ] Verify P&O is not mislabeled as ML/AI prediction.
- [ ] Commit `test: validate BioVolt scientific product copy`.

---

### Task 4: Operator workflow and action-safety audit

**Files:**
- Create: `docs/release/operator-journey.md`
- Modify: `docs/release/product-audit.md`

Walkthrough:

```text
open local operator view
-> authenticate if required
-> inspect device/calibration readiness
-> create/select experiment
-> start Passive/Manual/Adaptive as allowed
-> observe pending command
-> observe ACK/rejection and actual telemetry state
-> stop experiment
-> review Results/export
```

Audit:
- pending command is not confused with executed actuator state
- destructive/high-impact operations require deliberate action
- mode ownership is explicit
- manual override does not visually coexist with Adaptive ownership ambiguously
- no duplicate submission after network delay
- device-disconnected state prevents unsafe-looking controls
- calibration revision used by experiment is visible/recoverable

- [ ] Complete journey without undocumented workaround.
- [ ] Run once with a teammate who did not build the current UI.
- [ ] Record every hesitation/confusing control.
- [ ] Classify unsafe ambiguity around control execution as MAJOR/BLOCKER.
- [ ] Commit `docs: audit BioVolt operator workflow`.

---

### Task 5: Failure/recovery comprehension audit

**Files:**
- Modify: `docs/release/product-audit.md`
- Evidence: reuse Phase 9.2 failure screenshots

Audit these states:
- backend restart
- device/hotspot loss
- stale telemetry
- cached offline data
- sensor unavailable
- invalid/missing calibration
- public tunnel unavailable while local system healthy
- command rejection
- comparison ineligible

For each, a user must be able to answer:

```text
what happened?
is the displayed data current?
what remains safe/available?
what can I do next?
```

- [ ] Verify only one dominant diagnosis is presented.
- [ ] Verify raw stack traces are not the primary message.
- [ ] Verify recovery state clears only after actual fresh evidence.
- [ ] Verify public judge mode never suggests operator-only recovery action.
- [ ] Commit `test: audit BioVolt failure-state comprehension`.

---

### Task 6: Responsive layout audit

**Files:**
- Create: `docs/release/responsive-audit.md`
- Evidence: `release-evidence/screenshots/judge-mobile/`, `operator/`

Required viewports:

```text
phone portrait ~390 px
small tablet ~768 px
primary laptop ~1366 px
large presentation display >=1920 px
```

- [ ] Verify no critical KPI/status/control is clipped.
- [ ] Verify tables/results have a deliberate mobile strategy, not uncontrolled horizontal overflow.
- [ ] Verify charts retain readable axes/legend or provide compact alternative summary.
- [ ] Verify fixed banners/navigation do not cover content.
- [ ] Verify presentation display does not create excessive empty space that disconnects related information.
- [ ] Commit `docs: complete BioVolt responsive release audit`.

---

### Task 7: Accessibility audit

**Files:**
- Create: `docs/release/accessibility-audit.md`
- Modify frontend tests only when implementation defects are found

Audit:
- keyboard-only navigation
- visible focus
- logical tab order
- accessible names/descriptions
- status semantics/announcements for meaningful state changes
- no color-only meaning
- chart textual summaries
- reduced-motion support
- dialog focus trapping/restoration
- touch target sanity
- heading hierarchy

- [ ] Complete public judge journey keyboard-only.
- [ ] Complete operator core flow keyboard-only where controls are present.
- [ ] Run automated accessibility tooling available in project dependencies.
- [ ] Manually review status banners and charts because automated tools cannot validate scientific comprehension.
- [ ] Classify core-navigation or provenance/access-state accessibility blocker as MAJOR.
- [ ] Commit `docs: complete BioVolt accessibility release audit`.

---

### Task 8: Presentation/demo mode audit

**Files:**
- Create: `docs/release/presentation-audit.md`

The normal production UI should be presentation-ready without hiding scientific caveats.

Audit external-display use:
- primary KPI text readable from several feet away
- no tiny critical provenance/eligibility text
- Results comparison readable at a glance
- live/stale/simulation state still visible
- operator-only controls are not accidentally shown in public judge URL
- browser full-screen does not break navigation/recovery

Do not create a fake separate “marketing screen” with numbers not backed by real API data.

- [ ] Run on likely presentation display/projector if available.
- [ ] Capture one final judge Overview and one final Results screenshot.
- [ ] Commit `docs: audit BioVolt presentation experience`.

---

### Task 9: Ponytail product release gate

**Files:**
- Create: `scripts/release/phase9_product_gate.py`
- Create: `docs/release/product-release-checklist.md`

Convert findings to:

```text
BLOCKER / MAJOR / MINOR
owner phase/component
reproduction
expected state
actual state
resolution evidence
```

- [ ] Require zero BLOCKER.
- [ ] Require zero MAJOR.
- [ ] Require judge, operator, and recovery journeys to complete without undocumented workaround.
- [ ] Require responsive/accessibility audit PASS.
- [ ] Require final production screenshots after fixes.
- [ ] Emit `product-audit.md` into release evidence.
- [ ] Commit `test: add Ponytail BioVolt product release gate`.

## Exit Criteria

- [ ] Judge view is immediately understandable and visibly read-only.
- [ ] Information hierarchy reflects scientific/user priorities.
- [ ] Scientific claims/copy match actual eligibility.
- [ ] Operator workflow and command state are unambiguous.
- [ ] Failure/offline states communicate current data validity.
- [ ] Responsive and accessibility gates pass.
- [ ] Presentation mode remains truthful and readable.
- [ ] Zero BLOCKER and zero MAJOR Ponytail product findings remain.
