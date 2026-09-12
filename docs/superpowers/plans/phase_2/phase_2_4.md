# Phase 2.4: Recent History and Recharts Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add bounded live charts and recent persisted-history visualization without duplicating FastAPI scientific calculations.

**Architecture:** The chart layer receives complete `ProcessedTelemetryV1` frames from either the in-memory live buffer or the Phase 1 history endpoint. Chart adapters only select fields and format axes/tooltips. They do not derive scientific metrics.

**Tech Stack:** React, TypeScript, Recharts, Zustand, Fetch API, Vitest, React Testing Library.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Charts use backend-owned values exactly as provided.
- Frontend may transform timestamps into chart x-coordinates but must not derive scientific values.
- Live buffers remain capped at 1,200 frames/source.
- Phase 1 history API is bounded to at most 1,000 stored samples/request, so Phase 2 does not pretend to provide arbitrary long-duration history.
- Null data creates gaps in charts rather than zero-value points.
- Charts must remain readable without depending solely on color.

---

### Task 1: Define chart series adapters

**Files:**
- Create: `frontend/src/components/charts/series.ts`
- Create: `frontend/tests/components/test_chart_series.ts`

**Interfaces:**

```ts
export type TelemetryMetric =
  | 'voltage_mv'
  | 'current_ua'
  | 'power_uw'
  | 'cumulative_energy_mj'
  | 'od680'
  | 'temperature_c'
  | 'lux'

export interface ChartPoint {
  timestampMs: number
  value: number | null
}

export function metricSeries(frames: ProcessedTelemetryV1[], metric: TelemetryMetric): ChartPoint[]
```

- [ ] **Step 1: Write exact-field mapping test**

Given one frame with `power_uw=1.92`, mapping `power_uw` must return `1.92` exactly.

- [ ] **Step 2: Write null-preservation test**

OD680 null stays null. Do not map null to zero.

- [ ] **Step 3: Implement metric switch**

Only select the corresponding backend field and parse ISO timestamp to epoch milliseconds.

- [ ] **Step 4: Run and commit**

```bash
cd frontend
npm run test:run -- test_chart_series
git add src/components/charts/series.ts tests/components/test_chart_series.ts
git commit -m "feat: add BioVolt telemetry chart adapters"
```

---

### Task 2: Build reusable telemetry chart component

**Files:**
- Create: `frontend/src/components/charts/TelemetryChart.tsx`
- Create: `frontend/src/components/charts/chartMetadata.ts`
- Create: `frontend/tests/components/test_telemetry_chart.tsx`

**Interfaces:**

```ts
interface TelemetryChartProps {
  title: string
  unit: string
  points: ChartPoint[]
  emptyMessage: string
}
```

Metadata maps metric to display label/unit:

```text
voltage_mv -> BPV Voltage / mV
current_ua -> Current / µA
power_uw -> Power / µW
cumulative_energy_mj -> Cumulative Energy / mJ
od680 -> OD680 / unitless
temperature_c -> Temperature / °C
lux -> Light / lux
```

- [ ] **Step 1: Write empty-state test**

No points must render the supplied empty message and no invented chart line.

- [ ] **Step 2: Implement chart**

Use `ResponsiveContainer`, `LineChart`, `XAxis`, `YAxis`, `Tooltip`, and `Line`. Configure the line to preserve null gaps rather than connecting fabricated zeroes.

- [ ] **Step 3: Add accessible summary**

Each chart container requires a visible title and a short text summary indicating source/time range. Avoid claiming screen-reader support solely from SVG internals.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_telemetry_chart
git add src/components/charts tests/components/test_telemetry_chart.tsx
git commit -m "feat: add reusable BioVolt telemetry charts"
```

---

### Task 3: Add recent-history query hook

**Files:**
- Create: `frontend/src/hooks/useTelemetryHistory.ts`
- Create: `frontend/tests/lib/test_history_hook.tsx`

**Interfaces:**

```ts
export interface TelemetryHistoryState {
  data: ProcessedTelemetryV1[]
  loading: boolean
  error: string | null
  reload(): void
}

export function useTelemetryHistory(deviceId: string | null, cellId: string | null, limit: number): TelemetryHistoryState
```

- [ ] **Step 1: Write no-source test**

When device/cell is null, hook performs no fetch and returns empty data.

- [ ] **Step 2: Write abort-on-change test**

Changing source while a request is active aborts the previous request.

- [ ] **Step 3: Implement hook**

Clamp requested limit to `1..1000` before calling client. Do not silently request unsupported ranges.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_history_hook
git add src/hooks/useTelemetryHistory.ts tests/lib/test_history_hook.tsx
git commit -m "feat: load recent persisted BioVolt telemetry history"
```

---

### Task 4: Implement Charts page with explicit data modes

**Files:**
- Modify: `frontend/src/pages/ChartsPage.tsx`
- Create: `frontend/src/components/charts/ChartModeSelector.tsx`
- Create: `frontend/tests/app/test_charts_page.tsx`

**Interfaces:**

Chart modes:

```text
Live 60 s
Live 5 min
Live 10 min
Recent stored samples
```

`Recent stored samples` uses up to the most recent 1,000 persisted rows from Phase 1. It must not be labeled `1 hour` or another duration the backend cannot guarantee.

- [ ] **Step 1: Write mode-selection test**

With a 10-minute live buffer, `Live 60 s` filters by timestamp only for presentation and does not alter stored frames.

- [ ] **Step 2: Implement live-window filtering**

A helper may filter frames where `timestamp >= latestTimestamp - windowMs`. This is time-window presentation, not scientific recalculation.

- [ ] **Step 3: Render required charts**

At minimum:

```text
Power
BPV Voltage
Current
OD680
Temperature
Light
Cumulative Energy
```

If a metric is entirely null, render an explicit unavailable/no-valid-data state.

- [ ] **Step 4: Add recent-history mode**

Use `useTelemetryHistory` and keep live WebSocket state active while viewing history so returning to live requires no reconnect.

- [ ] **Step 5: Add source identity and timestamp range labels**

Every chart page view must identify the selected `device_id · cell_id` and whether data is `Live` or `Recent stored samples`.

- [ ] **Step 6: Run and commit**

```bash
npm run test:run -- test_charts_page
npm run typecheck
git add src/pages/ChartsPage.tsx src/components/charts/ChartModeSelector.tsx tests/app/test_charts_page.tsx
git commit -m "feat: visualize BioVolt live and recent telemetry history"
```

---

### Task 5: Add chart render-performance guardrails

**Files:**
- Create: `frontend/src/components/charts/selectWindow.ts`
- Create: `frontend/tests/components/test_chart_window.ts`

**Interfaces:**

```ts
export function selectTimeWindow(
  frames: ProcessedTelemetryV1[],
  windowMs: number,
): ProcessedTelemetryV1[]
```

- [ ] **Step 1: Write boundary test**

A frame exactly at the window lower bound is retained; an older frame is excluded.

- [ ] **Step 2: Preserve original array order**

Do not sort/mutate the Zustand live buffer in place.

- [ ] **Step 3: Verify maximum live input remains 1,200 frames**

The chart layer relies on store cap and must not copy unbounded historical arrays.

- [ ] **Step 4: Run full module quality gate**

```bash
npm run lint
npm run typecheck
npm run test:run
npm run build
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src frontend/tests
git commit -m "test: bound BioVolt chart history and render workload"
```

## Module 2.4 Exit Criteria

- [ ] Live voltage/current/power/OD680/temperature/lux/energy charts render.
- [ ] Null values remain chart gaps, not zeroes.
- [ ] Recent persisted history loads through REST only.
- [ ] UI does not claim history durations not guaranteed by Phase 1.
- [ ] Live 60 s, 5 min, and 10 min views use bounded in-memory data.
- [ ] Selected source and live/history mode are visible.
- [ ] No scientific value is recalculated in chart code.
- [ ] Tests, lint, typecheck, and build pass.
