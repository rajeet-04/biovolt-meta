# Phase 7.3: Analytics PWA Dashboard and Report UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a judge-readable experiment Results experience that leads with comparison eligibility and matched-window energy, then explains drivers, scientific outcomes, and data-quality caveats without duplicating backend analytics.

**Architecture:** `ExperimentResultsPage` consumes only Phase 7 analytics API resources. Recharts renders backend-aggregated series. Results components are pure presentation over API contracts. Synthetic, ineligible, extrapolated, stale, and low-coverage states are first-class UI states rather than hidden footnotes.

**Tech Stack:** React, TypeScript, Recharts, existing API/store patterns, Vitest, React Testing Library.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- No headline KPI calculation in frontend.
- No dual-y-axis chart for different physical units.
- Missing/ineligible KPI renders `Unavailable`, never numeric zero.
- Synthetic demo evidence must have persistent visible labeling on Results page.
- Gain card must show common duration and data-quality context.
- Statistical significance language is prohibited.
- Long charts use backend bucketed series and preserve missing gaps.
- Units are shown with every numeric summary.

---

### Task 1: Add analytics API/types and Results route

**Files:**
- Create: `frontend/src/types/analytics.ts`
- Create: `frontend/src/lib/analyticsApi.ts`
- Create: `frontend/src/pages/ExperimentResultsPage.tsx`
- Modify: `frontend/src/app/router.tsx`
- Test: `frontend/tests/analytics/ExperimentResultsPage.test.tsx`

Route:

```text
/experiments/:experimentId/results
```

- [ ] **Step 1: Define TS types mirroring summary/comparison/series responses**
- [ ] **Step 2: Write loading/error/not-completed tests**
- [ ] **Step 3: Implement route and summary fetch**
- [ ] **Step 4: Add Results navigation from completed experiment detail**
- [ ] **Step 5: Run and commit**

```bash
cd frontend
npm test -- ExperimentResultsPage
npm run typecheck
git add src/types/analytics.ts src/lib/analyticsApi.ts src/pages/ExperimentResultsPage.tsx src/app/router.tsx tests/analytics/ExperimentResultsPage.test.tsx
git commit -m "feat: add BioVolt experiment Results route"
```

---

### Task 2: Implement eligibility-first KPI summary

**Files:**
- Create: `frontend/src/components/analytics/ComparisonSummary.tsx`
- Create: `frontend/src/components/analytics/KpiCard.tsx`
- Create: `frontend/src/components/analytics/QualityBadge.tsx`
- Test: `frontend/tests/analytics/ComparisonSummary.test.tsx`

Top section displays:

```text
Experiment evidence badge
Passive matched energy
Adaptive matched energy
Matched-window gain % or Unavailable
Common duration
Passive coverage
Adaptive coverage
Quality eligibility status
```

When ineligible, `ComparisonSummary` lists human-readable reasons sourced from backend reason codes.

Synthetic behavior:
- persistent `Synthetic demo data` banner
- comparison numbers may be shown for engineering demonstration only
- headline copy must not say measured prototype improvement

- [ ] **Step 1: Write eligible positive/negative gain rendering tests**
- [ ] **Step 2: Write null/ineligible rendering test**
- [ ] **Step 3: Write synthetic banner test**
- [ ] **Step 4: Show common duration and coverage adjacent to gain**
- [ ] **Step 5: Run and commit**

```bash
npm test -- ComparisonSummary
npm run typecheck
git add src/components/analytics tests/analytics/ComparisonSummary.test.tsx
git commit -m "feat: summarize BioVolt matched-window experiment results"
```

---

### Task 3: Add electrical and control charts

**Files:**
- Create: `frontend/src/components/analytics/PowerChart.tsx`
- Create: `frontend/src/components/analytics/EnergyComparisonChart.tsx`
- Create: `frontend/src/components/analytics/ControlChart.tsx`
- Create: `frontend/tests/analytics/Charts.test.tsx`

Charts:
1. Power vs elapsed time, Passive and Adaptive on one shared µW axis.
2. Matched energy comparison as simple two-category bar or clearly labeled numeric comparison.
3. Grow LED PWM vs elapsed time on separate chart.
4. Mixer duty/state as separate event/step view if useful.

Rules:
- absent buckets create gaps, not interpolated line bridges
- axes include units
- tooltip shows elapsed time and values
- do not use dual y-axis to overlay PWM and power

- [ ] **Step 1: Write series-to-gap rendering tests where testable**
- [ ] **Step 2: Implement power chart**
- [ ] **Step 3: Implement energy comparison chart**
- [ ] **Step 4: Implement separate control chart**
- [ ] **Step 5: Run and commit**

```bash
npm test -- Charts
npm run typecheck
git add src/components/analytics/PowerChart.tsx src/components/analytics/EnergyComparisonChart.tsx src/components/analytics/ControlChart.tsx tests/analytics/Charts.test.tsx
git commit -m "feat: visualize BioVolt electrical and control experiment series"
```

---

### Task 4: Add scientific outcome and provenance sections

**Files:**
- Create: `frontend/src/components/analytics/ScientificOutcomes.tsx`
- Create: `frontend/src/components/analytics/CalibrationProvenance.tsx`
- Create: `frontend/src/components/analytics/DataQualityPanel.tsx`
- Test: `frontend/tests/analytics/ScientificOutcomes.test.tsx`
- Test: `frontend/tests/analytics/DataQualityPanel.test.tsx`

Scientific outcome display:
- OD680 start/end/change
- biomass concentration start/end/change
- dry biomass delta
- `Estimated CO2 biofixed into biomass`
- extrapolation caveat when relevant

Quality/provenance display:
- calibration revision
- baseline sequence/time
- sample/valid counts
- power coverage
- gap fraction/max gap
- temperature range
- analytics thresholds/method

- [ ] **Step 1: Write exact carbon wording test**
- [ ] **Step 2: Write missing scientific eligibility -> unavailable test**
- [ ] **Step 3: Write extrapolation caveat test**
- [ ] **Step 4: Implement quality/provenance panel**
- [ ] **Step 5: Run and commit**

```bash
npm test -- ScientificOutcomes DataQualityPanel
npm run typecheck
git add src/components/analytics/ScientificOutcomes.tsx src/components/analytics/CalibrationProvenance.tsx src/components/analytics/DataQualityPanel.tsx tests/analytics
git commit -m "feat: show BioVolt scientific outcomes and data provenance"
```

---

### Task 5: Add results-series selection and responsive hierarchy

**Files:**
- Modify: `frontend/src/pages/ExperimentResultsPage.tsx`
- Create: `frontend/src/components/analytics/SeriesSection.tsx`
- Test: `frontend/tests/analytics/ResultsHierarchy.test.tsx`

Page order:

```text
header/evidence/state
comparison eligibility + KPI cards
primary electrical chart
control drivers
scientific outcomes
quality/calibration provenance
export action
```

Responsive behavior:
- cards stack cleanly on narrow view
- chart containers have defined height and do not overflow viewport
- detailed quality sections may collapse behind clearly labeled disclosure controls, but headline caveats remain visible

- [ ] **Step 1: Write landmark/section-order accessibility test**
- [ ] **Step 2: Implement summary-first responsive layout**
- [ ] **Step 3: Fetch 5 or 10-second series by default for long runs; allow bounded bucket selector**
- [ ] **Step 4: Run and commit**

```bash
npm test -- ResultsHierarchy
npm run typecheck
npm run lint
git add src/pages/ExperimentResultsPage.tsx src/components/analytics/SeriesSection.tsx tests/analytics/ResultsHierarchy.test.tsx
git commit -m "feat: organize BioVolt Results for judge-first reading"
```

---

### Task 6: Add CSV export UX and copy safeguards

**Files:**
- Create: `frontend/src/components/analytics/ExportExperimentButton.tsx`
- Create: `frontend/tests/analytics/ExportExperimentButton.test.tsx`
- Create: `frontend/tests/analytics/ClaimLanguage.test.tsx`

- [ ] **Step 1: Link directly to backend export endpoint for current experiment**
- [ ] **Step 2: Use server-provided safe filename/content disposition where supported**
- [ ] **Step 3: Add tests asserting absence of `statistically significant`, `sequestered`, and unlabeled synthetic measured-result copy on Results components**
- [ ] **Step 4: Run full frontend suite/build and commit**

```bash
npm test
npm run typecheck
npm run lint
npm run build
git add src/components/analytics/ExportExperimentButton.tsx tests/analytics
git commit -m "test: safeguard BioVolt analytics export and claim language"
```

## Module 7.3 Exit Criteria

- [ ] Results page leads with eligibility and matched-window comparison.
- [ ] Gain is never computed in frontend.
- [ ] Synthetic demo state is persistent and unmistakable.
- [ ] Quality/coverage appears near headline result.
- [ ] Missing buckets are not visually invented.
- [ ] Charts avoid misleading dual-axis combinations.
- [ ] Scientific values retain exact Phase 5 wording/caveats.
- [ ] Provenance and CSV export are accessible from the same Results flow.
