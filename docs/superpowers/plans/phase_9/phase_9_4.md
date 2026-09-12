# Phase 9.4: Final Analytics, Demo, and Release-Candidate Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task-by-task. Apply Ponytail product-design reasoning to demo narrative, evidence traceability, fallback states, and judge comprehension. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify BioVolt's judge-facing analytics, rehearse the complete offline production demo, and issue the final release-candidate decision from explicit scientific, resilience, security, product, and analytics evidence.

**Architecture:** A standalone validator recomputes headline A/B metrics from persisted/exported experiment evidence and compares them with production API/UI outputs. The team then runs a timed production demo using the documented runbook, including truthful fallback paths. Release status is granted only when every preceding release gate passes and no headline claim lacks traceable provenance.

**Tech Stack:** Independent Python analytics scripts, CSV/SQLite exports, production API/PWA, Docker Compose, physical BioVolt hardware, release evidence pack.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints

- Production analytics are never validated by self-comparison alone.
- A/B improvement appears only when Phase 7 comparison eligibility is satisfied.
- Negative measured gain is a valid result and remains visible.
- Synthetic/demo evidence cannot satisfy a measured-performance release claim.
- Ineligible comparisons render `Unavailable` with reasons, never `0%`.
- Final primary rehearsal works without upstream internet.
- Every judge-facing headline number is traceable to experiment ID, evidence class, calibration revision where relevant, and export/raw evidence.
- Demo fallback never changes evidence class or hides a failure warning merely for presentation.
- Release status is binary `PASS` or `FAIL`; warnings cannot silently substitute for failed mandatory gates.

---

## Frozen Analytics Tolerances

Use these unless the actual stored/export precision defined in earlier phases requires tighter values. If a tolerance is technically incompatible with the stored/export representation, revise the representation or review the tolerance before release execution. Never widen a tolerance after seeing a mismatch.

```text
comparison_duration_s:
  exact equality after the API's documented normalization

passive_energy_mj, adaptive_energy_mj:
  absolute difference <= max(0.001 mJ, 0.1% of independent value)

gain_pct:
  absolute difference <= 0.05 percentage points

coverage/data-quality fractions:
  absolute difference <= 0.001

eligibility boolean, evidence_class, quality flags, reason codes:
  exact equality
```

---

### Task 1: Independent experiment-comparison recomputation

**Files:**
- Create: `scripts/release/recompute_experiment_comparison.py`
- Create: `tests/release/test_recompute_experiment_comparison.py`

Independent validator must not import production analytics modules.

Inputs:
- Passive experiment export/raw evidence
- Adaptive experiment export/raw evidence
- experiment metadata/provenance
- calibration references only where needed to validate exported derived data

Recompute:

```text
common elapsed comparison window
eligible observed intervals
passive cumulative energy over common window
adaptive cumulative energy over common window
coverage/data-quality metrics
gain_pct = (E_adaptive - E_passive) / E_passive * 100
```

Only compute gain when:
- Passive denominator > 0
- evidence classes satisfy Phase 7 requirements
- required overlap exists
- coverage/quality thresholds pass
- reboot/continuity rules pass

- [ ] Test positive gain.
- [ ] Test negative gain.
- [ ] Test zero/negative denominator.
- [ ] Test inadequate overlap/coverage.
- [ ] Test telemetry gap/reboot.
- [ ] Test measured vs synthetic evidence combinations.
- [ ] Return structured ineligibility reasons rather than a fake number.
- [ ] Commit `test: independently recompute BioVolt experiment comparisons`.

---

### Task 2: Compare independent analytics with production API and UI

**Files:**
- Create: `scripts/release/validate_production_analytics.py`
- Create: `docs/release/analytics-validation.md`

For selected release experiments compare:
- Passive energy
- Adaptive energy
- matched duration
- coverage/quality flags
- evidence class
- comparison eligibility
- gain percentage or Unavailable reason

Three-way agreement:

```text
independent recomputation
        ↕
production API
        ↕
production PWA headline
```

- [ ] Fetch production analytics API result.
- [ ] Recompute independently from exports/raw evidence.
- [ ] Compare using frozen tolerances.
- [ ] Verify UI headline matches API semantics/value and documented rounding.
- [ ] Verify ineligible comparison shows the same core reason code/category.
- [ ] Verify negative result remains negative in UI.
- [ ] Verify simulation experiment cannot appear as measured gain.
- [ ] Classify headline disagreement as BLOCKER.
- [ ] Emit `analytics-recompute.json`.
- [ ] Commit `test: validate BioVolt production analytics independently`.

---

### Task 3: Evidence traceability audit

**Files:**
- Create: `scripts/release/validate_claim_traceability.py`
- Create: `docs/release/claim-traceability.md`

Create a trace table for every demo headline claim:

| Claim | UI field | API field | Experiment | Evidence class | Calibration revision | Export/raw source |
|---|---|---|---|---|---|---|
| BPV power | ... | ... | ... | measured | electrical calibration | ... |
| OD680 | ... | ... | ... | measured | optical revision | ... |
| estimated biomass | ... | ... | ... | measured | biomass regression revision | ... |
| estimated CO2 biofixed | ... | ... | ... | measured | biomass/volume/baseline | ... |
| adaptive energy gain | ... | ... | Passive + Adaptive IDs | measured | relevant revisions | ... |

- [ ] Every headline demo metric has a trace.
- [ ] Missing trace makes that claim unavailable for the final demo.
- [ ] Verify historical measured experiment is clearly historical, not presented as current live output.
- [ ] Verify synthetic fallback trace says `synthetic_demo`.
- [ ] Commit `test: validate BioVolt judge-claim traceability`.

---

### Task 4: Build Ponytail final demo narrative/runbook

**Files:**
- Create: `docs/release/demo-runbook.md`
- Create: `docs/release/demo-recovery-cards.md`
- Create: `docs/release/demo-storyboard.md`

The demo is a product/scientific narrative, not a feature tour.

Recommended primary sequence:

```text
1. Problem and system in one sentence
2. Show real device connection + live evidence state
3. Show BPV voltage and backend-derived current/power
4. Explain OD680 path and calibration only if valid
5. Show active/recorded Passive experiment
6. Show Adaptive P&O behavior and local firmware safety ownership
7. Open Results matched comparison
8. Show eligibility/provenance and one supporting chart
9. Export/trace evidence
10. Demonstrate that core system works without upstream internet
```

Ponytail narrative rules:
- every screen answers one main question
- do not open every navigation item
- reveal technical depth only when it supports the current claim
- keep provenance visible while explaining outcome
- do not call P&O machine learning
- do not imply a gain before Results eligibility proves it
- preserve failure/read-only/evidence banners even during presentation

- [ ] Write exact operator actions and expected visible checkpoints.
- [ ] Mark which steps require live wet hardware response and which may use completed measured history.
- [ ] Set a target duration for each section.
- [ ] Commit `docs: add Ponytail BioVolt final demo narrative`.

---

### Task 5: Define truthful fallback ladder

**Files:**
- Modify: `docs/release/demo-runbook.md`
- Modify: `docs/release/demo-recovery-cards.md`

Fallback priority:

```text
A. Live real hardware + measured current experiment
B. Real hardware live telemetry + previously completed measured Results
C. Previously completed measured experiment history if wet response is slow
D. Explicit Simulation / demo data only if real hardware is unavailable
```

Rules:
- B/C never claim historical data is the current run
- D never claims measured gain
- fallback reason is stated briefly and clearly, not hidden
- internet/Cloudflared failure should normally require no fallback because local demo remains functional

Recovery cards include:
- backend restart
- ESP32 reconnect
- hotspot problem
- stale dashboard
- invalid calibration
- sensor unavailable
- public tunnel failure

Each card states:

```text
symptom
expected visible UI state
one or two recovery actions
what NOT to do
when to switch to the next fallback level
```

- [ ] Rehearse each fallback once.
- [ ] Ensure no fallback requires source-code editing.
- [ ] Commit `docs: define BioVolt truthful demo fallback ladder`.

---

### Task 6: Timed offline judge rehearsal

**Files:**
- Create: `docs/release/demo-rehearsal.md`

Primary rehearsal conditions:
- production build
- real hardware available
- upstream internet disabled
- no IDE/source editing required
- documented runbook used by operator/team

- [ ] Start from Phase 9.2 cold-start state.
- [ ] Time startup-to-ready.
- [ ] Time each demo segment.
- [ ] Target core judged sequence <=5 minutes unless official event slot is known to differ; update this timing before execution, not mid-rehearsal.
- [ ] Require no undocumented command/source edit.
- [ ] Have a teammate who did not author the current implementation follow the runbook.
- [ ] Record ambiguous instructions and fix the product/runbook before final rehearsal.
- [ ] Verify every spoken headline metric is traceable.
- [ ] Inject one benign failure and recover using the documented recovery card.
- [ ] Repeat until the critical flow requires no improvisation.
- [ ] Commit `docs: record BioVolt final offline demo rehearsal`.

---

### Task 7: Final public-security and secret-leak recheck

**Files:**
- Create: `scripts/release/validate_release_security.py`

- [ ] Require Phase 8 public penetration matrix PASS on release build.
- [ ] Verify `/ws/device` is not publicly reachable.
- [ ] Verify public mutation requests fail.
- [ ] Search tracked release/config/evidence files for secret names and accidental values.
- [ ] Verify public API/export does not expose device token, PIN/PIN hash, Wi-Fi credentials, or tunnel token.
- [ ] Classify any public write or secret exposure as BLOCKER.
- [ ] Commit `test: revalidate BioVolt release security boundary`.

---

### Task 8: Aggregate final release gate

**Files:**
- Create: `scripts/release/phase9_release_gate.py`
- Create: `docs/release/release-checklist.md`

Mandatory inputs:

```text
Phase 9.1 scientific gate PASS
Phase 9.2 resilience/safety gate PASS
Phase 9.3 Ponytail product gate PASS
Phase 8 public-security acceptance PASS
independent analytics PASS
claim traceability PASS
production contract/backend/frontend/firmware tests PASS
secret-leak check PASS
BLOCKER count = 0
MAJOR count = 0
```

- [ ] Read machine-readable gate outputs where available.
- [ ] Fail closed when a required report is missing.
- [ ] Emit final JSON with `status: PASS|FAIL` and failed-gate list.
- [ ] Do not convert missing evidence into warning-only success.
- [ ] Commit `test: add BioVolt final release-candidate gate`.

---

### Task 9: Release evidence aggregation and freeze

**Files:**
- Modify: `README.md`
- Create: `docs/release/release-candidate.md`
- Create: `scripts/release/build_evidence_index.py`

Record accepted versions:
- git revision
- firmware build/version
- backend/frontend/schema expectations
- calibration revisions used for final measured experiments
- production startup command
- required environment preparation
- known MINOR limitations

- [ ] Build evidence index linking all non-sensitive reports/screenshots.
- [ ] Verify evidence pack contains no secrets.
- [ ] Require final gate PASS before marking release candidate.
- [ ] Tag/version publication only after team review of evidence.
- [ ] Commit `docs: freeze BioVolt release-candidate configuration`.

## Exit Criteria

- [ ] Independent A/B analytics agree with production within frozen tolerances.
- [ ] Ineligible, negative, and synthetic comparisons are represented honestly.
- [ ] Every headline judge claim is traceable to provenance/evidence.
- [ ] Ponytail demo narrative and fallback ladder are documented and rehearsed.
- [ ] Primary demo succeeds with upstream internet disabled.
- [ ] Public security and secret checks pass on the release build.
- [ ] All scientific, resilience, product, analytics, security, and regression gates pass.
- [ ] Zero BLOCKER and zero MAJOR issues remain.
- [ ] BioVolt is ready to freeze as a release candidate.
