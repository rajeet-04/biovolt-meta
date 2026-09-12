# Phase 2.3: Overview and Live Data Screens Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the judge-facing Overview and Live Data screens using only backend-owned processed telemetry and explicit live/stale/offline status.

**Architecture:** Page components consume selectors from the Zustand store. Reusable metric/status components own formatting and presentation. Scientific values are never recomputed in UI components.

**Tech Stack:** React, TypeScript, Tailwind CSS, Zustand, React Testing Library.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Metric cards display backend values only.
- Null values render `Unavailable`, never zero.
- Units are explicit and consistent.
- Live/stale/disconnected states must be visible without relying only on color.
- Selected device/cell source is shown in the UI.
- Processed telemetry `sequence` is preserved and visible in the Live Data inspection view.
- Simulator and hardware sources are treated identically.

---

### Task 1: Add scientific formatting helpers

**Files:**
- Create: `frontend/src/lib/format.ts`
- Create: `frontend/tests/lib/test_format.ts`

**Interfaces:**

```ts
export function formatNullableNumber(value: number | null, digits: number): string
export function formatTimestamp(value: string): string
export function formatMode(mode: 'monitor' | 'passive' | 'adaptive' | 'manual'): string
```

- [ ] **Step 1: Write null-format test**

```ts
expect(formatNullableNumber(null, 2)).toBe('Unavailable')
```

- [ ] **Step 2: Write finite-number tests**

Reject accidental `NaN`/infinite display by returning `Unavailable` for non-finite numbers even if TypeScript nominally says `number`.

- [ ] **Step 3: Implement helpers**

Use `Intl.DateTimeFormat` for local display while preserving full ISO timestamp in title/accessibility text where useful.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_format
git add src/lib/format.ts tests/lib/test_format.ts
git commit -m "feat: add BioVolt scientific display formatters"
```

---

### Task 2: Add freshness/status helpers and indicators

**Files:**
- Create: `frontend/src/lib/stale.ts`
- Create: `frontend/src/components/status/ConnectionBadge.tsx`
- Create: `frontend/src/components/status/FreshnessBadge.tsx`
- Create: `frontend/tests/components/test_status_badges.tsx`

**Interfaces:**

```ts
export function telemetryAgeMs(timestamp: string, nowMs: number): number
export function isTelemetryStale(timestamp: string, nowMs: number, thresholdMs?: number): boolean
```

Default stale threshold: `3000` ms.

- [ ] **Step 1: Write threshold-boundary tests**

Telemetry at 2,999 ms is fresh; 3,001 ms is stale.

- [ ] **Step 2: Implement badges**

Text states include:

```text
Live
Stale
Backend reconnecting
Backend disconnected
```

Do not use color as the only distinction.

- [ ] **Step 3: Run and commit**

```bash
npm run test:run -- test_status_badges
git add src/lib/stale.ts src/components/status tests/components
git commit -m "feat: show BioVolt telemetry freshness and connection state"
```

---

### Task 3: Build reusable metric cards

**Files:**
- Create: `frontend/src/components/metrics/MetricCard.tsx`
- Create: `frontend/src/components/metrics/MetricGrid.tsx`
- Create: `frontend/tests/components/test_metric_card.tsx`

**Interfaces:**

```ts
interface MetricCardProps {
  label: string
  value: number | null
  digits: number
  unit: string
  description?: string
}
```

- [ ] **Step 1: Write null-value test**

A null metric must visibly render `Unavailable` and still show its metric label.

- [ ] **Step 2: Write unit test**

Example voltage value `438.2` renders with `mV`; power renders with `µW`.

- [ ] **Step 3: Implement card/grid**

Cards must remain readable at laptop and narrow widths. No sparklines in this module.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_metric_card
git add src/components/metrics tests/components/test_metric_card.tsx
git commit -m "feat: add BioVolt telemetry metric cards"
```

---

### Task 4: Build source selector

**Files:**
- Create: `frontend/src/components/status/SourceSelector.tsx`
- Create: `frontend/tests/components/test_source_selector.tsx`

**Interfaces:**
- Consumes available source keys from store.
- Produces user selection through `selectSource`.

- [ ] **Step 1: Write one-source behavior test**

With one source, display its device/cell identity without forcing an unnecessary dropdown interaction.

- [ ] **Step 2: Write multi-source selection test**

With two sources, user can switch and selected value persists in store.

- [ ] **Step 3: Implement source labels**

Display exact identity such as:

```text
biovolt-01 · cell-a
```

Never label a source `Simulator` based on ID.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_source_selector
git add src/components/status/SourceSelector.tsx tests/components/test_source_selector.tsx
git commit -m "feat: add BioVolt telemetry source selection"
```

---

### Task 5: Implement Overview page

**Files:**
- Modify: `frontend/src/pages/OverviewPage.tsx`
- Create: `frontend/src/components/status/TelemetryHeader.tsx`
- Create: `frontend/tests/app/test_overview_page.tsx`

**Interfaces:**
- Uses currently selected source.
- Displays latest backend frame.

Required metrics when available:

```text
BPV Voltage           mV
Current               µA
Power                 µW
Cumulative Energy     mJ
OD680                 unitless
Temperature           °C
Light                 lux
Grow LED PWM          raw 0-255
Mixer                 On/Off
Control Mode          text
```

Biomass/CO2 fields may be shown only when non-null and must preserve wording `Estimated CO2 biofixed into biomass`.

- [ ] **Step 1: Write no-source empty-state test**

Render a clear message such as `Waiting for BioVolt telemetry` and connection status. Do not render zeros.

- [ ] **Step 2: Write populated-page test**

Feed one processed telemetry frame and assert voltage/current/power/OD680 are the exact backend values after display formatting.

- [ ] **Step 3: Write nullable-energy test**

Feed a valid processed frame with `cumulative_energy_mj: null` and assert the card renders `Unavailable`, not `0 mJ`.

- [ ] **Step 4: Implement page**

Top area shows selected source, connection state, telemetry freshness, and timestamp. Metric grid follows.

- [ ] **Step 5: Add actuator/control summary**

Show LED PWM, mixer, and mode as observed state only. Do not add controls/buttons that send commands.

- [ ] **Step 6: Run and commit**

```bash
npm run test:run -- test_overview_page
git add src/pages/OverviewPage.tsx src/components/status/TelemetryHeader.tsx tests/app/test_overview_page.tsx
git commit -m "feat: build BioVolt live overview dashboard"
```

---

### Task 6: Implement Live Data page

**Files:**
- Modify: `frontend/src/pages/LiveDataPage.tsx`
- Create: `frontend/src/components/metrics/TelemetryFieldTable.tsx`
- Create: `frontend/tests/app/test_live_data_page.tsx`

**Interfaces:**
- Displays latest processed telemetry as grouped human-readable fields.

Groups:

```text
Electrical
Biological
Environment
Actuators
Control
Identity/Freshness
```

- [ ] **Step 1: Write exact-field rendering test**

Assert at least `device_id`, `cell_id`, `sequence`, timestamp, voltage, current, power, cumulative energy, OD680, temperature, lux, LED PWM, mixer, and mode appear.

- [ ] **Step 2: Write null biological-value test**

Null biomass/carbon values must render `Unavailable` without hiding the fact that those metrics are currently uncalibrated/unavailable.

- [ ] **Step 3: Implement grouped table**

Use semantic table or definition-list markup. Include units in labels/value cells. Sequence is identity/ordering metadata and has no physical unit.

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
git commit -m "feat: add BioVolt live telemetry inspection screen"
```

## Module 2.3 Exit Criteria

- [ ] Overview renders no fake values while waiting for telemetry.
- [ ] Current/power/OD680 are displayed from backend payload, not recalculated.
- [ ] Nullable cumulative energy and other null fields render `Unavailable`.
- [ ] Source identity and freshness are visible.
- [ ] Device stale and socket disconnected are distinguishable.
- [ ] Live Data page exposes required processed telemetry fields including `sequence`.
- [ ] Actuator state is observational only.
- [ ] Source selector is device-source neutral.
- [ ] Tests, lint, typecheck, and build pass.
