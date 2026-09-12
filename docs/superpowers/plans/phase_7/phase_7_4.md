# Phase 7.4: Independent Analytics Validation and Reporting Acceptance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently verify BioVolt headline analytics from exported experiment data, validate negative/ineligible cases, and prove the PWA/reporting layer cannot turn synthetic, incomplete, or low-quality data into an unsupported success claim.

**Architecture:** Validation uses a standalone Python script that reads exported CSV and recomputes the Phase 7 KPI chain without importing production analytics functions. Deterministic fixtures establish exact expected results. A measured-experiment evidence template compares backend API output against the independent recomputation and records data-quality caveats before judge-facing use.

**Tech Stack:** Python standard library plus pandas only if explicitly added for validation, pytest fixtures, PWA tests, CSV export.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Independent validator must not import `biovolt_backend.analytics.*` calculation functions.
- A positive Adaptive result is not a pass criterion. Negative or null measured results are valid outcomes and must render honestly.
- Synthetic fixtures verify software behavior only.
- A measured result is judge-facing only when experiment `evidence_class=measured` and comparison quality gates pass.
- Validation reproduces common matched duration, energy, gain, coverage, and gap handling.
- No p-values, significance labels, or inferential confidence intervals are added during validation.

---

### Task 1: Add independent analytics validation script

**Files:**
- Create: `scripts/validate_phase7_analytics.py`
- Create: `scripts/phase7_analytics_validation.md`

CLI:

```bash
python scripts/validate_phase7_analytics.py \
  --csv experiment.csv \
  --passive-arm <id> \
  --adaptive-arm <id>
```

Independent script responsibilities:

```text
read CSV
validate experiment/arm identity and modes
validate evidence class
compute elapsed seconds from experiment start
select common matched duration
select rows within matched duration
identify uptime reset/reboot
calculate first/last cumulative energy per arm
calculate matched energy by difference
calculate gain percent when passive energy > 0
calculate sample/valid power counts
calculate configured coverage metric
detect gaps using supplied/default gap threshold
recompute start/end scientific outcomes when fields available
print eligibility reasons and comparison
```

The script must use its own direct formulas and not call backend analytics helpers.

- [ ] **Step 1: Implement CSV schema validation and arm selection**
- [ ] **Step 2: Implement independent matched-window and energy calculation**
- [ ] **Step 3: Implement coverage/gap/reboot checks**
- [ ] **Step 4: Implement optional scientific start/end summary**
- [ ] **Step 5: Print machine-readable JSON option for CI evidence**
- [ ] **Step 6: Exit non-zero on internal inconsistency or requested strict comparison mismatch**
- [ ] **Step 7: Document usage and evidence fields**
- [ ] **Step 8: Commit**

```bash
git add scripts/validate_phase7_analytics.py scripts/phase7_analytics_validation.md
git commit -m "test: independently validate BioVolt experiment analytics"
```

---

### Task 2: Add deterministic known-result analytics fixtures

**Files:**
- Create: `backend/tests/fixtures/analytics/positive_gain.csv`
- Create: `backend/tests/fixtures/analytics/negative_gain.csv`
- Create: `backend/tests/fixtures/analytics/unequal_duration.csv`
- Create: `backend/tests/fixtures/analytics/gapped.csv`
- Create: `backend/tests/fixtures/analytics/reboot.csv`
- Create: `backend/tests/fixtures/analytics/synthetic.csv`
- Create: `backend/tests/analytics/test_known_fixtures.py`

Required fixture expectations:

```text
positive_gain       -> exact +20.0% expected gain
negative_gain       -> valid negative percentage
unequal_duration    -> uses shorter common elapsed duration
gapped              -> fails or caveats based on configured coverage threshold
reboot               -> ineligible
synthetic            -> engineering metrics available, measured headline blocked
```

- [ ] **Step 1: Create small human-reviewable fixture rows with hand-computable cumulative energy**
- [ ] **Step 2: Test production analytics result against known expected values**
- [ ] **Step 3: Run independent validator against the same fixtures**
- [ ] **Step 4: Ensure both implementations agree within explicit floating tolerance**
- [ ] **Step 5: Commit**

```bash
cd backend
pytest tests/analytics/test_known_fixtures.py -v
cd ..
python scripts/validate_phase7_analytics.py --csv backend/tests/fixtures/analytics/positive_gain.csv --passive-arm passive --adaptive-arm adaptive
git add backend/tests/fixtures/analytics backend/tests/analytics/test_known_fixtures.py
git commit -m "test: add known-result BioVolt analytics fixtures"
```

---

### Task 3: Add comparison edge-case regression tests

**Files:**
- Modify: `backend/tests/analytics/test_comparison.py`
- Create: `backend/tests/integration/test_analytics_edge_cases.py`

Cases:
- passive energy exactly zero
- missing cumulative energy endpoint row
- power coverage below threshold
- large telemetry gap
- one arm shorter than the other
- one arm with reboot
- completed experiment with no Adaptive arm
- multiple candidate Passive/Adaptive arms requiring explicit selection
- scientific metrics unavailable while electrical comparison remains valid

- [ ] **Step 1: Add zero-denominator result is null with `nonpositive_passive_energy`**
- [ ] **Step 2: Add no silent arm guessing test**
- [ ] **Step 3: Add quality threshold boundary tests**
- [ ] **Step 4: Add electrical-valid/scientific-unavailable test**
- [ ] **Step 5: Run and commit**

```bash
cd backend
pytest tests/analytics/test_comparison.py tests/integration/test_analytics_edge_cases.py -v
git add tests/analytics/test_comparison.py tests/integration/test_analytics_edge_cases.py
git commit -m "test: cover BioVolt analytics eligibility edge cases"
```

---

### Task 4: Add PWA reporting and claim-language acceptance

**Files:**
- Create: `frontend/tests/analytics/ReportingAcceptance.test.tsx`
- Modify: existing Results components only if tests expose defects

Assertions:
- ineligible gain displays `Unavailable` and reasons, not `0%`
- negative gain displays negative value honestly
- synthetic evidence has persistent `Synthetic demo data` labeling
- synthetic results never use `Measured improvement` or equivalent language
- exact wording `Estimated CO2 biofixed into biomass`
- no `statistically significant`, `p-value`, or inferential confidence copy
- common duration and coverage remain visible near gain
- reboot/low-coverage caveats cannot be hidden behind only a tooltip

- [ ] **Step 1: Write all claim-language/state tests**
- [ ] **Step 2: Correct any result components that violate the contract**
- [ ] **Step 3: Run frontend analytics suite**
- [ ] **Step 4: Commit**

```bash
cd frontend
npm test -- ReportingAcceptance
npm run typecheck
npm run lint
git add tests/analytics/ReportingAcceptance.test.tsx src/components/analytics src/pages/ExperimentResultsPage.tsx
git commit -m "test: enforce BioVolt analytics reporting integrity"
```

---

### Task 5: Define measured experiment acceptance evidence template

**Files:**
- Create: `scripts/phase7_measured_experiment_acceptance.md`

For each intended judge-facing comparison, record:

```text
experiment_id
passive_arm_id
adaptive_arm_id
evidence_class
passive_calibration_revision_id
adaptive_calibration_revision_id
passive baseline sequence/time
adaptive baseline sequence/time
common_duration_s
passive power coverage
adaptive power coverage
passive gap fraction/max gap
adaptive gap fraction/max gap
passive matched energy_mj
adaptive matched energy_mj
backend gain_pct
independent gain_pct
absolute/relative validation difference
scientific outcome eligibility
biomass extrapolation flags
known caveats
result status: eligible | ineligible
```

Rule:
- If backend and independent values disagree beyond documented numerical tolerance, result is blocked from judge-facing use until resolved.
- If measured gain is negative, retain it. Do not replace it with a previous/synthetic positive result.
- If result is ineligible, display the reason rather than falling back to a synthetic result without explicit synthetic labeling.

- [ ] **Step 1: Write evidence template and pass/block criteria**
- [ ] **Step 2: Add explicit negative-result handling rule**
- [ ] **Step 3: Add measured-vs-synthetic fallback labeling rule**
- [ ] **Step 4: Commit**

```bash
git add scripts/phase7_measured_experiment_acceptance.md
git commit -m "docs: define BioVolt measured analytics acceptance evidence"
```

---

### Task 6: Phase 7 full regression gate

Run:

```bash
pytest shared/tests -v
cd backend && pytest -v
cd ../simulator && pytest -v
cd ../frontend && npm test && npm run typecheck && npm run lint && npm run build
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
```

Then validate at least one deterministic fixture with the independent script. When real Passive/Adaptive experiment data exist, run the same independent validator on that export before judge-facing use.

- [ ] **Step 1: Run complete software/firmware regression**
- [ ] **Step 2: Run independent validator on known-result fixture**
- [ ] **Step 3: Verify backend/validator tolerance agreement**
- [ ] **Step 4: Verify synthetic reporting remains labeled**
- [ ] **Step 5: Verify no result path requires positive gain to pass**

## Module 7.4 Exit Criteria

- [ ] Headline energy/gain can be independently recomputed from exported data.
- [ ] Known fixtures cover positive, negative, unequal-duration, gap, reboot, and synthetic cases.
- [ ] Zero Passive denominator never produces infinity or fake zero gain.
- [ ] Negative measured gain is represented honestly.
- [ ] Synthetic evidence cannot masquerade as measured evidence.
- [ ] PWA contains no significance/inferential language unsupported by replicate design.
- [ ] Measured judge-facing result requires API/independent agreement and quality eligibility.
- [ ] Full Phase 0 to 7 regression passes before production packaging begins.
