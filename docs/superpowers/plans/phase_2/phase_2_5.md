# Phase 2.5: Offline PWA, Dexie Cache, Reconnect, and Resync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the BioVolt dashboard installable and useful without external internet while preventing stale cached scientific data from masquerading as live telemetry.

**Architecture:** `vite-plugin-pwa` caches the application shell/static assets. Dexie/IndexedDB stores a bounded local copy of processed telemetry and selected-source UI state. Runtime connectivity is determined by backend WebSocket/REST reachability, not merely `navigator.onLine`. On reconnect, the app resynchronizes with backend latest/history before clearing cached/stale banners.

**Tech Stack:** vite-plugin-pwa, Workbox through plugin configuration, Dexie, IndexedDB, Zustand, React.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Service worker must not cache `/api/*` scientific responses for transparent replay.
- WebSocket data is never service-worker cached.
- Cached telemetry is explicitly labeled `Cached` with its original timestamp.
- Offline/cached mode must not display `Live`.
- Dexie cache stores processed telemetry only, never raw device tokens or secrets.
- Cached scientific values are never recalculated in the frontend.
- Cache is bounded and pruned.
- Reconnect/resync behavior is source-neutral and works for simulator or hardware.

---

### Task 1: Configure installable PWA manifest and service worker

**Files:**
- Modify: `frontend/vite.config.ts`
- Create: `frontend/public/biovolt-mark.svg`
- Create: `frontend/src/pwa/registerPwa.ts`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/tests/app/test_pwa_config.ts`

**Interfaces:**
- App name: `BioVolt`
- Short name: `BioVolt`
- Display: `standalone`
- Theme/background align with dashboard dark theme.
- Start URL: `/`

- [ ] **Step 1: Add static BioVolt mark asset**

Use a simple original leaf/lightning mark in SVG. Keep it project-owned and dependency-free.

- [ ] **Step 2: Configure `VitePWA`**

Use `registerType: 'autoUpdate'`. Precache static build assets only. Configure navigation fallback for application routes.

Explicitly exclude API routes from runtime caching. Do not define a NetworkFirst/StaleWhileRevalidate rule for `/api`.

- [ ] **Step 3: Add service-worker registration module**

Expose UI-safe update state but do not force reload while the user is reading telemetry. An available update may show a nonblocking refresh prompt later.

- [ ] **Step 4: Add configuration test**

Inspect `vite.config.ts` or exported config to verify manifest name/start URL and absence of API runtime-cache pattern.

- [ ] **Step 5: Build and commit**

```bash
cd frontend
npm run test:run
npm run build
git add vite.config.ts public src/pwa src/main.tsx tests/app/test_pwa_config.ts
git commit -m "feat: make BioVolt dashboard an installable PWA"
```

---

### Task 2: Define Dexie database and cached telemetry schema

**Files:**
- Create: `frontend/src/db/appDb.ts`
- Create: `frontend/src/db/telemetryCache.ts`
- Create: `frontend/tests/db/test_telemetry_cache.ts`

**Interfaces:**

```ts
export interface CachedTelemetryRow {
  key: string
  source_key: string
  timestamp: string
  received_cache_at: string
  payload: ProcessedTelemetryV1
}

export interface UiStateRow {
  key: 'selected_source'
  value: string
}
```

Dexie stores:

```text
telemetry_cache: key, source_key, timestamp
ui_state: key
```

- [ ] **Step 1: Write cache round-trip test**

Insert one processed frame and retrieve it without changing scientific values.

- [ ] **Step 2: Implement cache key**

Use deterministic composite string:

```text
<device_id>::<cell_id>::<timestamp>
```

- [ ] **Step 3: Add `cacheTelemetry(frame)`**

Store exact payload and cache-write timestamp.

- [ ] **Step 4: Add `loadCachedTelemetry(sourceKey, limit)`**

Return newest rows in chronological order for display. Enforce bounded `limit`.

- [ ] **Step 5: Add selected-source persistence helpers**

`saveSelectedSource` and `loadSelectedSource` persist only the source key.

- [ ] **Step 6: Run and commit**

```bash
npm run test:run -- test_telemetry_cache
git add src/db tests/db
git commit -m "feat: cache BioVolt processed telemetry in IndexedDB"
```

---

### Task 3: Add bounded cache-write throttle and pruning

**Files:**
- Modify: `frontend/src/db/telemetryCache.ts`
- Create: `frontend/tests/db/test_cache_pruning.ts`

**Interfaces:**
- At most approximately one cache write/second/source during normal live operation.
- Keep maximum 3,600 cached rows/source, approximately one hour at 1 Hz.

- [ ] **Step 1: Write throttle test**

Frames for same source at cache times 0 ms, 500 ms, and 1,050 ms result in two cache writes.

- [ ] **Step 2: Write prune test**

After inserting over 3,600 rows for one source, prune oldest rows for that source and keep newest 3,600.

- [ ] **Step 3: Implement throttle state**

Use a small module-local map keyed by source. It controls cache writes only, not live Zustand ingest.

- [ ] **Step 4: Implement pruning transaction**

Prune asynchronously without blocking every WebSocket frame. Trigger after successful cache writes on a bounded cadence such as every 60 writes/source.

- [ ] **Step 5: Run and commit**

```bash
npm run test:run -- test_cache_pruning
git add src/db/telemetryCache.ts tests/db/test_cache_pruning.ts
git commit -m "feat: bound BioVolt local telemetry cache"
```

---

### Task 4: Integrate cache with live telemetry store

**Files:**
- Modify: `frontend/src/hooks/useDashboardSocket.ts`
- Modify: `frontend/src/stores/telemetryStore.ts`
- Create: `frontend/tests/integration/test_live_cache.tsx`

**Interfaces:**
- Every valid live frame immediately updates Zustand.
- Eligible frames are asynchronously persisted by cache throttle.
- Cache failures do not break live telemetry.

- [ ] **Step 1: Write live-first test**

Use a deliberately delayed fake cache write. Assert store updates before cache promise resolves.

- [ ] **Step 2: Write cache-failure isolation test**

If IndexedDB/cache write rejects, frame remains live in store and socket stays connected. Record a nonfatal cache status if desired.

- [ ] **Step 3: Implement cache call after ingest**

Do not await cache write in the WebSocket message handler.

- [ ] **Step 4: Persist user source selection**

Store selection after explicit user change. On application initialization, restore it only if the source later becomes available or cached.

- [ ] **Step 5: Run and commit**

```bash
npm run test:run -- test_live_cache
git add src/hooks src/stores tests/integration/test_live_cache.tsx
git commit -m "feat: persist BioVolt live telemetry cache without blocking UI"
```

---

### Task 5: Implement offline cached-data mode

**Files:**
- Create: `frontend/src/hooks/useCachedTelemetry.ts`
- Create: `frontend/src/components/status/OfflineBanner.tsx`
- Modify: `frontend/src/pages/OverviewPage.tsx`
- Modify: `frontend/src/pages/ChartsPage.tsx`
- Create: `frontend/tests/app/test_offline_mode.tsx`

**Interfaces:**
- Cached mode activates when backend live connection is unavailable and cached data exists.
- `OfflineBanner` text includes the last cached telemetry timestamp.

- [ ] **Step 1: Write cached-banner test**

Expected visible copy includes `Showing cached data` and a timestamp. It must not contain `Live`.

- [ ] **Step 2: Implement cached-data hook**

Load cached selected source when socket/backend state is disconnected. Do not overwrite newer live data if connectivity returns during the query.

- [ ] **Step 3: Render cached overview state**

Metric cards may show cached payload but freshness status must identify it as cached/stale.

- [ ] **Step 4: Render cached charts**

Charts may use Dexie cache with explicit `Cached` mode label.

- [ ] **Step 5: Run and commit**

```bash
npm run test:run -- test_offline_mode
git add src/hooks/useCachedTelemetry.ts src/components/status/OfflineBanner.tsx src/pages tests/app/test_offline_mode.tsx
git commit -m "feat: show explicit offline cached BioVolt telemetry"
```

---

### Task 6: Implement reconnect resynchronization

**Files:**
- Create: `frontend/src/hooks/useReconnectResync.ts`
- Modify: `frontend/src/app/App.tsx`
- Create: `frontend/tests/integration/test_reconnect_resync.tsx`

**Interfaces:**
- Trigger when WebSocket transitions from disconnected/connecting to connected.
- For selected source, fetch latest plus recent history after connection is restored.

- [ ] **Step 1: Write one-resync-per-reconnect test**

A state sequence `disconnected -> connecting -> connected` triggers one resync, not two.

- [ ] **Step 2: Implement resync order**

1. fetch system status
2. if selected source exists, fetch latest
3. fetch recent history
4. ingest latest into live store only if it is newer than stored latest
5. retain history for charts/cache

- [ ] **Step 3: Abort obsolete resync**

If selected source changes during resync, abort old source requests.

- [ ] **Step 4: Keep cached banner until verified live frame/state**

Do not clear cached/offline indication merely because browser `navigator.onLine` becomes true.

- [ ] **Step 5: Run full module quality gate**

```bash
npm run lint
npm run typecheck
npm run test:run
npm run build
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src frontend/tests
git commit -m "feat: resynchronize BioVolt PWA after backend reconnect"
```

## Module 2.5 Exit Criteria

- [ ] PWA builds with manifest and service worker.
- [ ] Static app shell works after external internet is disabled.
- [ ] Scientific REST responses are not silently service-worker cached.
- [ ] Processed telemetry is cached in IndexedDB at bounded cadence.
- [ ] Cache is bounded to 3,600 rows/source.
- [ ] Live UI updates are not blocked by IndexedDB.
- [ ] Cached data is visibly labeled cached with original timestamp.
- [ ] Cached mode never claims `Live`.
- [ ] Reconnect performs backend resynchronization.
- [ ] Cache failures do not crash or disconnect live telemetry.
- [ ] Tests, lint, typecheck, and build pass.
