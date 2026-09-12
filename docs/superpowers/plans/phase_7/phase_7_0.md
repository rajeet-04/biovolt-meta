# Phase 7 Overview: Experiment Analytics, A/B Comparison, and Scientific Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert completed BioVolt experiments into reproducible, quality-gated Passive-vs-Adaptive comparisons, scientific outcome summaries, time-series views, and exports without fabricating statistical certainty.

**Architecture:** FastAPI owns every experiment KPI and quality rule. Analytics operate on persisted calibrated telemetry, experiment metadata, calibration provenance, and continuity information. The PWA requests summary/series/comparison resources and renders them without recomputing headline metrics. Comparison uses a common elapsed-time window across eligible arms. A backend evidence-class stamp distinguishes measured runs from explicitly synthetic demo/test runs without adding source-type fields to raw telemetry.

**Tech Stack:** FastAPI, SQLAlchemy/SQLite, Python analytics domain functions, React/TypeScript/Recharts, CSV export, pytest/Vitest.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 6 Adaptive experiments and Phase 5 calibrated scientific pipeline.

## KPI Contract

Every KPI implementation must define:
- name
- business/scientific question
- exact formula
- units
- source fields
- aggregation grain
- eligibility rule
- null rule
- comparison window
- data-quality guardrails

No frontend-only headline calculation is allowed.

---

## Primary Decision KPI

### Matched-window electrical energy gain

**Question:** Over the same observed elapsed duration, how much more or less electrical energy did the Adaptive arm produce than the Passive arm?

```text
matched_window_energy_gain_pct =
  (adaptive_energy_mj - passive_energy_mj)
  / passive_energy_mj * 100
```

Units: percent.

Eligibility:
- one completed Passive arm and one completed Adaptive arm selected
- both have calibrated `power_uw`/cumulative-energy provenance
- both have a positive common elapsed comparison duration
- both have no device reboot within the selected comparison window
- passive matched-window energy > 0
- each arm meets configurable minimum observed-power coverage
- neither experiment/evidence set is marked `synthetic_demo` for judge-facing measured-result presentation

Default MVP quality guardrail:

```text
minimum_power_coverage_fraction = 0.80
```

This is an operational data-completeness threshold, not a universal scientific/statistical standard. It is backend configuration and is displayed with the result provenance.

If eligibility fails, the KPI is `null` with explicit reasons.

---

## Comparison Window

For each arm define elapsed seconds relative to experiment `started_at`.

```text
arm_observed_end_elapsed = last eligible sample timestamp - experiment started_at
common_duration_s = min(passive_observed_end_elapsed, adaptive_observed_end_elapsed)
```

Only samples in:

```text
0 <= elapsed_s <= common_duration_s
```

participate in comparison.

The dashboard must display `common_duration_s`. It must not compare full 30-minute Adaptive energy with 20-minute Passive energy and call the ratio gain.

---

## Energy Calculation Source

Preferred matched-window energy calculation uses persisted gap-safe cumulative energy when one uninterrupted device boot spans the comparison window:

```text
arm_energy_mj = last_cumulative_energy_mj - first_cumulative_energy_mj
```

with arm-specific first/last rows within the matched window.

If cumulative energy reset/decreases inside the window, mark the arm ineligible rather than silently stitching boot sessions. A reboot during an experiment is itself a quality failure because firmware returns to Monitor-safe after reboot.

---

## Driver Metrics

Per arm:

```text
mean_power_uw
median_power_uw
min_power_uw
max_power_uw
matched_window_energy_mj
energy_per_hour_mj_h = energy_mj / observed_hours
mean_grow_led_pwm
led_pwm_change_count
mixer_on_fraction
valid_power_sample_count
power_coverage_fraction
telemetry_gap_fraction
```

These explain why the primary metric moved. They are not substitutes for the primary matched-window energy comparison.

---

## Scientific Outcome Metrics

When eligible:

```text
starting_od680
ending_od680
od680_change
starting_biomass_g_l
ending_biomass_g_l
biomass_concentration_change_g_l
starting_dry_biomass_g
ending_dry_biomass_g
biomass_delta_g
estimated_co2_biofixed_g
```

CO2 remains a calibrated biomass-derived estimate with the Phase 5 wording and provenance.

Do not present short-term optical movement as permanent carbon sequestration.

---

## Data Quality Metrics

Per arm:

```text
sample_count
valid_power_sample_count
power_coverage_fraction
sensor_validity fractions
gap_count
gap_seconds
telemetry_gap_fraction
maximum_gap_seconds
calibration_revision_id
biomass_extrapolation_fraction
temperature_min_c
temperature_max_c
temperature_out_of_configured_range_fraction
```

Nominal persisted cadence is approximately 1 Hz. Define a backend-configured analytics gap threshold, initially:

```text
analytics_gap_threshold_s = 2.5
```

Intervals larger than this count toward telemetry gap seconds. This threshold is an operational interpretation of the persistence cadence and must be documented in summary provenance.

---

## Evidence Class

Add experiment-level immutable evidence metadata:

```text
evidence_class = measured | synthetic_demo
```

It is stamped from backend deployment configuration when the experiment is created and cannot be changed after `ready`.

Purpose:
- real hardware profile -> `measured`
- deterministic simulator/demo profile -> `synthetic_demo`

This is experiment provenance only. Do not add `source_type` to `device-telemetry.v1` or branch backend telemetry logic by hardware vs simulator.

Synthetic analytics may still be useful for demo/testing but every analytics response and PWA view must visibly label them synthetic and block measured-result headline language.

---

## Statistical Rule

Hackathon MVP analytics are descriptive.

Allowed:
- observed differences
- means/medians
- matched-window energy difference/percent
- quality coverage
- calibration diagnostics

Not allowed without a separately designed independent-replicate methodology:
- p-values
- `statistically significant`
- confidence intervals presented as inferential evidence
- claims of general causal improvement beyond the measured prototype run

If later replicate data are added, design that analysis separately rather than treating 1 Hz telemetry rows as independent biological replicates.

---

## Module Map

### Module 7.1: Analytics Domain and Data-Quality Model
Plan: `docs/superpowers/plans/phase_7/phase_7_1.md`

Produces:
- evidence-class provenance
- elapsed/matched-window selection
- arm quality summaries
- gap/coverage calculations
- energy/driver/scientific pure KPI functions
- eligibility reasons

### Module 7.2: Experiment Analytics Service, API, and Export
Plan: `docs/superpowers/plans/phase_7/phase_7_2.md`

Produces:
- summary endpoint
- bucketed series endpoint
- Passive/Adaptive comparison endpoint
- quality endpoint/model
- provenance-rich CSV export
- query bounds and aggregation tests

### Module 7.3: Analytics PWA Dashboard and Report UX
Plan: `docs/superpowers/plans/phase_7/phase_7_3.md`

Produces:
- experiment Results route
- KPI summary-first hierarchy
- matched-window energy comparison
- power/energy/control/scientific charts
- quality/provenance panel
- explicit synthetic/caveat states
- CSV download UX

### Module 7.4: Independent Analytics Validation and Reporting Acceptance
Plan: `docs/superpowers/plans/phase_7/phase_7_4.md`

Produces:
- independent CSV recomputation script
- known-data analytics fixture tests
- no-significance/synthetic-label checks
- measured experiment acceptance template
- Phase 7 regression gate

---

## Planned API Surface

```text
GET /api/experiments/{id}/analytics/summary
GET /api/experiments/{id}/analytics/series?bucket_s=5
GET /api/experiments/{id}/analytics/comparison?passive_arm_id=...&adaptive_arm_id=...
GET /api/experiments/{id}/analytics/export.csv
```

Summary response includes:

```text
experiment metadata
evidence_class
calibration provenance
arm summaries
quality metrics
headline comparison eligibility
headline comparison value or null
eligibility reasons
analytics configuration provenance
```

---

## Series Aggregation Rules

For long charts, backend buckets source rows by elapsed-time bucket.

Within a bucket:
- timestamp/elapsed = bucket start or center, documented
- power = mean and optional min/max
- voltage = mean
- OD/biomass = mean of eligible non-null values
- grow LED PWM = mean
- mixer = on fraction
- no interpolation across missing buckets

Frontend never draws a continuous bridge across an absent bucket without visually marking the gap.

---

## Product Design Requirements

Results page should answer in this order:

```text
1. Was the experiment data eligible and trustworthy enough to compare?
2. What happened to matched-window electrical energy?
3. What drove that result?
4. What happened to biomass/CO2 estimate, if scientifically eligible?
5. What are the calibration/data-quality caveats?
6. How can the underlying data be exported?
```

Default dashboard should not lead with dozens of charts.

Recommended top section:
- experiment state/evidence badge
- Passive energy
- Adaptive energy
- matched-window gain when eligible
- common duration
- quality status

No dual-y-axis chart for unrelated units. Separate power, OD/biomass, temperature, and control charts when needed.

## Data Analytics Display Rules

- show unit on every KPI
- show comparison denominator/context
- display `Unavailable` plus reason instead of 0 for invalid KPIs
- show common comparison duration
- show coverage/gaps near headline result
- preserve meaningful precision only; do not show excessive decimals
- no synthetic measured-result headline
- no statistical significance language

## Planned Commit Sequence

1. `feat: define BioVolt experiment analytics and quality metrics`
2. `feat: expose BioVolt analytics API and export`
3. `feat: add BioVolt experiment results dashboard`
4. `test: independently validate BioVolt experiment analytics`

## Phase 7 Exit Criteria

- [ ] Every headline KPI has a documented formula/unit/eligibility rule.
- [ ] Passive/Adaptive energy comparison uses a matched elapsed window.
- [ ] Passive denominator must be positive.
- [ ] Reboot/reset within comparison window makes result ineligible.
- [ ] Data coverage and gaps are calculated and displayed.
- [ ] Synthetic demo experiments are visibly labeled and cannot masquerade as measured evidence.
- [ ] Frontend does not independently recompute headline analytics.
- [ ] Invalid KPI renders unavailable, not zero.
- [ ] Biomass/CO2 preserves Phase 5 provenance/caveats.
- [ ] No p-value/significance/CI is fabricated from telemetry samples.
- [ ] CSV export includes experiment, mode, calibration, evidence, quality, and telemetry provenance.
- [ ] Independent validation recomputes headline energy/gain from exported data.
- [ ] Existing Phase 0 to 6 regression suites remain green.

## Handoff to Phase 8

Phase 8 packages the local system for one-command production deployment and adds an optional, separately constrained read-only public judge surface through Nginx and Cloudflared.
