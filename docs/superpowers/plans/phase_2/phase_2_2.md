# Phase 2.2: Backend Client, Runtime Guards, and Live State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the PWA to the stable Phase 1 REST and `/ws/dashboard` interfaces using explicit TypeScript types, runtime validation, reconnect logic, and a source-neutral Zustand store.

**Architecture:** `lib/api.ts` owns REST transport, `lib/dashboardSocket.ts` owns WebSocket lifecycle, `types/` mirrors backend-owned processed telemetry and system-status responses, and `stores/telemetryStore.ts` owns normalized live UI state keyed by `(device_id, cell_id)`. No component talks directly to `fetch` or `WebSocket`.

**Tech Stack:** TypeScript, browser Fetch API, browser WebSocket API, Zustand, Vitest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- The frontend must consume processed telemetry and never raw ESP32 telemetry.
- The frontend must not recalculate current, power, OD680, biomass, carbon, or energy.
- The runtime guard rejects structurally invalid WebSocket messages before store mutation.
- The backend URL defaults to same-origin paths so later Nginx routing requires no frontend rewrite.
- Vite development proxy may route `/api` and `/ws` to FastAPI.
- Reconnect delay is bounded and testable.
- No simulator imports, simulator ID matching, or source-specific labels.

---

### Task 1: Define frontend API types

**Files:**
- Create: `frontend/src/types/telemetry.ts`
- Create: `frontend/src/types/system.ts`
- Create: `frontend/tests/lib/test_telemetry_guard.ts`

**Interfaces:**

```ts
export interface ProcessedTelemetryV1 {
  schema_version: 1
  device_id: string
  cell_id: string
  timestamp: string
  electrical: {
    voltage_mv: number | null
    current_ua: number | null
    power_uw: number | null
    load_resistance_ohm: number
    cumulative_energy_mj: number
  }
  biological: {
    od680: number | null
    biomass_g_l: number | null
    biomass_total_g: number | null
    biomass_delta_g: number | null
    co2_biofixed_g: number | null
  }
  environment: {
    temperature_c: number | null
    lux: number | null
  }
  actuators: {
    grow_led_pwm: number
    mixer_on: boolean
  }
  control: {
    mode: 'monitor' | 'passive' | 'adaptive' | 'manual'
  }
}
```

`SystemStatus` mirrors the Phase 1 `/api/system/status` response.

- [ ] **Step 1: Write failing runtime-guard tests**

Cover one valid processed payload and invalid cases for missing `device_id`, wrong `schema_version`, non-object `electrical`, and string-valued `power_uw`.

- [ ] **Step 2: Implement `isProcessedTelemetryV1(value: unknown): value is ProcessedTelemetryV1`**

Use small reusable helpers such as `isRecord`, `isNullableNumber`, and exact control-mode checking. Do not coerce strings into numbers.

- [ ] **Step 3: Add system-status interfaces**

Include backend/database status, connected device IDs, count, and telemetry freshness fields from Phase 1.

- [ ] **Step 4: Run tests and commit**

```bash
cd frontend
npm run test:run -- test_telemetry_guard
npm run typecheck
git add src/types tests/lib
git commit -m "feat: define BioVolt frontend telemetry contracts"
```

---

### Task 2: Implement REST API client

**Files:**
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/tests/lib/test_api.ts`
- Modify: `frontend/vite.config.ts`

**Interfaces:**

```ts
export interface TelemetryHistoryQuery {
  deviceId: string
  cellId: string
  limit?: number
}

export async function getSystemStatus(signal?: AbortSignal): Promise<SystemStatus>
export async function getLatestTelemetry(deviceId: string, cellId: string, signal?: AbortSignal): Promise<ProcessedTelemetryV1>
export async function getTelemetryHistory(query: TelemetryHistoryQuery, signal?: AbortSignal): Promise<ProcessedTelemetryV1[]>
```

- [ ] **Step 1: Write failing URL-construction tests**

Verify query parameters are encoded exactly and history limit defaults to 100 when omitted by the caller or is intentionally omitted so backend default applies. Choose one behavior and document it. Recommended: omit unless caller specifies.

- [ ] **Step 2: Implement `ApiError`**

Expose `status: number`, `path: string`, and safe response detail when JSON detail exists.

- [ ] **Step 3: Implement fetch wrapper**

Use same-origin `/api/...` paths by default. Reject non-2xx responses. Validate telemetry response shapes with the runtime guard before returning.

- [ ] **Step 4: Add Vite development proxy**

Proxy:

```text
/api -> http://localhost:8000
/ws  -> ws://localhost:8000
```

Enable WebSocket proxying for `/ws`.

- [ ] **Step 5: Run tests and commit**

```bash
npm run test:run -- test_api
npm run typecheck
git add src/lib/api.ts tests/lib/test_api.ts vite.config.ts
git commit -m "feat: add typed BioVolt backend REST client"
```

---

### Task 3: Implement source-neutral Zustand telemetry store

**Files:**
- Create: `frontend/src/stores/telemetryStore.ts`
- Create: `frontend/tests/stores/test_telemetry_store.ts`

**Interfaces:**

```ts
export type SourceKey = `${string}::${string}`

export interface TelemetrySourceState {
  latest: ProcessedTelemetryV1
  liveBuffer: ProcessedTelemetryV1[]
}

export interface TelemetryStoreState {
  sources: Record<SourceKey, TelemetrySourceState>
  selectedSource: SourceKey | null
  wsState: 'connecting' | 'connected' | 'disconnected'
  lastSocketError: string | null
  ingest(frame: ProcessedTelemetryV1): void
  selectSource(source: SourceKey): void
  setWsState(state: TelemetryStoreState['wsState']): void
}
```

- [ ] **Step 1: Write failing ingest test**

Ingest one frame and assert it becomes both `latest` and the first live-buffer item under `device_id::cell_id`.

- [ ] **Step 2: Write source-selection test**

First source auto-selects only when `selectedSource` is null. A later source must not steal selection.

- [ ] **Step 3: Write bounded-buffer test**

Ingest 1,205 frames and assert only the newest 1,200 remain.

- [ ] **Step 4: Implement store**

Do not derive scientific values. Store exact backend payloads.

- [ ] **Step 5: Run and commit**

```bash
npm run test:run -- test_telemetry_store
git add src/stores tests/stores
git commit -m "feat: add source-neutral BioVolt telemetry store"
```

---

### Task 4: Implement reconnecting dashboard WebSocket client

**Files:**
- Create: `frontend/src/lib/dashboardSocket.ts`
- Create: `frontend/tests/lib/test_dashboard_socket.ts`

**Interfaces:**

```ts
export interface DashboardSocketHandlers {
  onTelemetry(frame: ProcessedTelemetryV1): void
  onState(state: 'connecting' | 'connected' | 'disconnected'): void
  onInvalidMessage(raw: string): void
}

export class DashboardSocketClient {
  start(): void
  stop(): void
}

export function reconnectDelay(attempt: number): number
```

- [ ] **Step 1: Write reconnect-delay test**

Expected milliseconds:

```text
1000, 2000, 4000, 8000, 10000, 10000...
```

- [ ] **Step 2: Write URL-construction test**

For page protocol `http:` use `ws:`. For `https:` use `wss:`. Same host and `/ws/dashboard` path.

- [ ] **Step 3: Write invalid-message test**

Malformed JSON or structurally invalid processed telemetry calls `onInvalidMessage` and never calls `onTelemetry`.

- [ ] **Step 4: Implement WebSocket lifecycle**

On open reset reconnect attempt. On close schedule bounded retry unless `stop()` was called. Do not create parallel socket instances.

- [ ] **Step 5: Run and commit**

```bash
npm run test:run -- test_dashboard_socket
git add src/lib/dashboardSocket.ts tests/lib/test_dashboard_socket.ts
git commit -m "feat: add resilient BioVolt dashboard websocket client"
```

---

### Task 5: Wire hooks and application lifecycle

**Files:**
- Create: `frontend/src/hooks/useDashboardSocket.ts`
- Create: `frontend/src/hooks/useSystemStatus.ts`
- Modify: `frontend/src/app/App.tsx`
- Create: `frontend/tests/app/test_runtime_wiring.tsx`

**Interfaces:**
- `useDashboardSocket()` starts one dashboard connection for the mounted app.
- `useSystemStatus()` polls `/api/system/status` every 5 seconds while app is active.

- [ ] **Step 1: Write one-socket lifecycle test**

Mount/unmount twice with a fake client factory and assert each mount creates one client and each unmount calls `stop()`.

- [ ] **Step 2: Implement hook wiring**

Incoming valid telemetry calls store `ingest`. Connection states update store.

- [ ] **Step 3: Implement bounded status polling**

Use `AbortController` on cleanup. Do not overlap polls if the previous request is still running.

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
git commit -m "feat: connect BioVolt PWA runtime to backend telemetry"
```

---

### Task 6: Add device-source-neutrality architecture test

**Files:**
- Create: `frontend/tests/architecture/test_source_neutrality.ts`

**Interfaces:**
- Test scans `frontend/src` for prohibited simulator coupling.

- [ ] **Step 1: Implement architecture scan**

Reject source strings containing:

```text
biovolt_simulator
biovolt-sim-
is_simulated
source_type
```

except inside the architecture test itself.

- [ ] **Step 2: Assert no frontend dependency on simulator package**

Read `frontend/package.json` and ensure no simulator package is listed.

- [ ] **Step 3: Run and commit**

```bash
npm run test:run
git add tests/architecture/test_source_neutrality.ts
git commit -m "test: enforce source-neutral BioVolt frontend"
```

## Module 2.2 Exit Criteria

- [ ] Processed telemetry and status are typed.
- [ ] Invalid WebSocket payloads never mutate store state.
- [ ] REST client uses same-origin API paths.
- [ ] Development proxy supports REST and WebSocket backend access.
- [ ] Live state is keyed by device/cell source.
- [ ] Live buffers are capped at 1,200 frames/source.
- [ ] Dashboard WebSocket reconnects with bounded backoff.
- [ ] App starts/stops socket cleanly.
- [ ] Status polling is bounded and cancellable.
- [ ] Frontend contains no simulator dependency or simulator-specific source branch.
- [ ] No scientific values are recalculated in frontend code.
- [ ] Tests, lint, typecheck, and build pass.
