# Phase 2.6: Responsive, Accessible, and Failure-Safe UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the BioVolt PWA for hackathon-demo use across laptop and mobile widths, keyboard interaction, backend failures, empty telemetry, stale telemetry, and component/runtime errors.

**Architecture:** Accessibility and failure states are implemented as reusable primitives rather than page-specific patches. The application shell owns route-level error containment, status components own live/stale/offline semantics, and layout components own responsive behavior.

**Tech Stack:** React, TypeScript, Tailwind CSS, React Testing Library, Vitest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- The primary target is a laptop dashboard, but mobile/narrow layouts must remain usable.
- Status must never be conveyed only by color.
- Keyboard users can reach navigation, selectors, and interactive chart/history controls.
- Reduced-motion preference is respected.
- Unexpected render errors must not blank the entire application without a recovery path.
- Backend unavailability, no device connected, no telemetry yet, stale telemetry, and cached/offline mode must be distinguishable states.
- No error state invents scientific values.

---

### Task 1: Implement global error boundary

**Files:**
- Create: `frontend/src/app/ErrorBoundary.tsx`
- Modify: `frontend/src/app/App.tsx`
- Create: `frontend/tests/app/test_error_boundary.tsx`

**Interfaces:**
- `ErrorBoundary` catches descendant render errors.
- Fallback contains BioVolt title, concise failure copy, and a `Reload application` button.

- [ ] **Step 1: Write failing render-error test**

Create a test component that throws and assert fallback is rendered instead of propagating to a blank page.

- [ ] **Step 2: Implement boundary**

Do not expose stack traces or secrets in user-facing fallback text.

- [ ] **Step 3: Add reload action test**

Mock `window.location.reload` through a testable injected callback or wrapper rather than relying on an unmockable global implementation.

- [ ] **Step 4: Run and commit**

```bash
cd frontend
npm run test:run -- test_error_boundary
git add src/app/ErrorBoundary.tsx src/app/App.tsx tests/app/test_error_boundary.tsx
git commit -m "feat: add BioVolt application error boundary"
```

---

### Task 2: Define canonical application data states

**Files:**
- Create: `frontend/src/components/status/DataStatePanel.tsx`
- Create: `frontend/src/lib/dataState.ts`
- Create: `frontend/tests/components/test_data_state.tsx`

**Interfaces:**

```ts
export type DataState =
  | 'loading'
  | 'no_device'
  | 'waiting_telemetry'
  | 'live'
  | 'stale'
  | 'disconnected'
  | 'cached'
  | 'error'
```

- [ ] **Step 1: Write state-resolution tests**

Examples:

```text
no connected device + no cache -> no_device
connected device + no telemetry -> waiting_telemetry
socket connected + fresh telemetry -> live
socket connected + telemetry age > 3 s -> stale
socket disconnected + cache exists -> cached
```

- [ ] **Step 2: Implement pure `resolveDataState(...)`**

Inputs must be explicit booleans/timestamps, not direct browser globals.

- [ ] **Step 3: Implement `DataStatePanel` copy**

Each non-live state has distinct text. Cached state includes last-data time where provided.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_data_state
git add src/components/status/DataStatePanel.tsx src/lib/dataState.ts tests/components/test_data_state.tsx
git commit -m "feat: standardize BioVolt live stale and offline states"
```

---

### Task 3: Harden responsive navigation and metric layout

**Files:**
- Modify: `frontend/src/components/layout/AppShell.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/components/layout/TopBar.tsx`
- Modify: `frontend/src/components/metrics/MetricGrid.tsx`
- Create: `frontend/tests/components/test_responsive_shell.tsx`

**Interfaces:**
- Desktop/laptop: persistent sidebar.
- Narrow layout: collapsible menu controlled by labeled button.

- [ ] **Step 1: Write menu semantics test**

Assert mobile menu button has accessible name `Open navigation`, toggles `aria-expanded`, and becomes `Close navigation` while open.

- [ ] **Step 2: Implement responsive classes**

Metric grid target:

```text
1 column narrow mobile
2 columns medium
3 or 4 columns laptop/desktop depending available width
```

Avoid fixed widths that force horizontal page scrolling.

- [ ] **Step 3: Ensure charts can scroll only inside intended containers if needed**

The main page must not require horizontal viewport scrolling at 390 px width.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_responsive_shell
git add src/components/layout src/components/metrics tests/components/test_responsive_shell.tsx
git commit -m "feat: make BioVolt dashboard responsive"
```

---

### Task 4: Add keyboard and status accessibility

**Files:**
- Modify: `frontend/src/components/status/ConnectionBadge.tsx`
- Modify: `frontend/src/components/status/FreshnessBadge.tsx`
- Modify: `frontend/src/components/status/SourceSelector.tsx`
- Modify: `frontend/src/components/charts/ChartModeSelector.tsx`
- Create: `frontend/tests/components/test_accessibility_semantics.tsx`

**Interfaces:**
- Connection/freshness changes are announced through a bounded `aria-live="polite"` region.
- Source and chart-mode controls use native select/buttons where possible.

- [ ] **Step 1: Write accessible-name tests**

Verify source selector and chart mode selector have associated labels.

- [ ] **Step 2: Add polite status announcement**

Avoid announcing every 500 ms metric update. Only connection/freshness state transitions enter the live region.

- [ ] **Step 3: Verify keyboard activation**

Use `userEvent.tab()` and keyboard selection/activation in tests.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_accessibility_semantics
git add src/components tests/components/test_accessibility_semantics.tsx
git commit -m "feat: improve BioVolt dashboard keyboard and status accessibility"
```

---

### Task 5: Add loading/error boundaries around REST-driven regions

**Files:**
- Modify: `frontend/src/pages/SystemPage.tsx`
- Modify: `frontend/src/pages/ChartsPage.tsx`
- Create: `frontend/src/components/status/RetryPanel.tsx`
- Create: `frontend/tests/app/test_rest_failure_states.tsx`

**Interfaces:**
- REST errors render localized retry UI without destroying live WebSocket telemetry state.

- [ ] **Step 1: Write history-failure isolation test**

If recent-history fetch fails, live metric/store data remains present and Charts page offers retry.

- [ ] **Step 2: Write status-failure test**

System page distinguishes `Backend unreachable` from `No devices connected`.

- [ ] **Step 3: Implement retry component**

A native button invokes a provided retry callback. It must not reload the entire app for recoverable REST failures.

- [ ] **Step 4: Run and commit**

```bash
npm run test:run -- test_rest_failure_states
git add src/pages src/components/status/RetryPanel.tsx tests/app/test_rest_failure_states.tsx
git commit -m "feat: isolate BioVolt REST failure states"
```

---

### Task 6: Add render-performance regression tests

**Files:**
- Create: `frontend/tests/stores/test_live_buffer_performance.ts`
- Create: `frontend/tests/components/test_metric_render_stability.tsx`

**Interfaces:**
- Store stays capped at 1,200 frames/source.
- Metric components receive only selected latest frame values, not entire history arrays.

- [ ] **Step 1: Assert 10,000 ingests remain bounded**

Ingest 10,000 generated processed frames into one source and verify buffer length remains exactly 1,200.

- [ ] **Step 2: Assert overview selector does not expose full buffer when only latest is required**

Prefer narrow Zustand selectors to avoid avoidable rerenders.

- [ ] **Step 3: Run complete module quality gate**

```bash
npm run lint
npm run typecheck
npm run test:run
npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src frontend/tests
git commit -m "test: harden BioVolt dashboard reliability and render bounds"
```

## Module 2.6 Exit Criteria

- [ ] Application-level render error produces a recoverable fallback.
- [ ] Loading, no-device, waiting, live, stale, disconnected, cached, and error states are distinct.
- [ ] Mobile/narrow layout remains usable without page-wide horizontal scrolling.
- [ ] Navigation and selectors are keyboard operable.
- [ ] Connection state changes use accessible text and polite announcements.
- [ ] Metric updates do not spam aria-live regions.
- [ ] REST failures are localized and retryable.
- [ ] 10,000 telemetry ingests still leave a 1,200-frame source buffer.
- [ ] Tests, lint, typecheck, and build pass.
