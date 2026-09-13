# Live telemetry motion

## Intent

Make the live dashboard feel current and consequential while preserving the
operator's ability to read values, gaps, and source provenance. The current
overview already has one restrained first-load reveal and the status layer
polls at a deliberate cadence. The main motion risk is the chart renderer: a
live series updates frequently, so any implicit chart tween can compete with
the data itself.

## Findings

### 1. Live charts need an explicit update policy

- Location: `frontend/src/components/charts/TelemetryChart.tsx:1-9`
- Current behavior: every chart renders a Recharts `Line` over a
  `ResponsiveContainer`; the live page feeds it a moving buffer, but the chart
  does not declare whether updates should animate.
- Risk: default renderer behavior may repeatedly interpolate a frequently
  changing series. That can make small changes look more dramatic than they
  are and can make null gaps harder to parse.
- Target: pass an explicit live-update policy from `ChartsPage` to
  `TelemetryChart`. For live modes, disable repeated series tweening and keep
  `connectNulls={false}`. For stored history, either use the same stable render
  or allow one short entry animation only when the dataset changes because the
  mode/source changed.
- Suggested values: live series `isAnimationActive={false}`; any intentional
  history entry motion no longer than `180ms`, `ease-out`, and never looping.
- Verification: with the simulator running, observe the same chart through at
  least ten incoming frames; the line should update without a visible sweep or
  reset, and null samples must remain gaps. Switch between live and history and
  confirm the first view remains readable with `prefers-reduced-motion: reduce`.

### 2. Freshness is already legible; do not add a global pulse

- Location: `frontend/src/components/status/FreshnessBadge.tsx:10-29`
- Current behavior: the badge recalculates age every `250ms` when it owns the
  clock and communicates `Live`/`Stale` with text plus a marker.
- Risk: adding a CSS pulse here would turn a useful status indicator into a
  constant attention attractor, especially beside live charts.
- Target: keep the existing timer and text semantics. If visual motion is
  needed later, animate only the transition into `Stale`, once, with a short
  opacity/scale change and a reduced-motion fallback.
- Suggested values: one-shot `150-200ms`, `ease-out`; no infinite animation.
- Verification: hold a fixture across the stale threshold and confirm the text
  and non-color signal change even when motion is disabled.

### 3. First-load reveal is appropriately bounded

- Location: `frontend/src/styles/index.css:106-120`
- Current behavior: `.overview-page` runs `overview-arrive` once for `260ms`
  using a small `6px` vertical offset, with a global reduced-motion override at
  lines `122-130`.
- Assessment: retain this single authored arrival moment. It establishes
  orientation without animating every card, and the reduced-motion rule is
  already present.
- Target if revisited: keep the offset at or below `8px`, duration between
  `220-280ms`, and do not cascade staggered child animations across the
  overview.
- Verification: reload the overview once, then navigate between pages; confirm
  there is no repeated child choreography and that reduced motion removes the
  reveal.

## Implementation sequence

1. Add a `live` prop to `TelemetryChart` and pass it from `ChartsPage` based on
   the selected mode.
2. Make the chart animation behavior explicit, preserving the existing null
   gap and tooltip contracts.
3. Verify desktop and narrow layouts with the simulator, then repeat with
   reduced motion enabled.

## Scope boundary

This is a plan, not an implementation. The `improve-animations` skill is an
advisor/audit workflow and does not edit application source; execute this plan
as a separate, explicitly reviewed change so chart motion decisions remain
testable and reversible.
