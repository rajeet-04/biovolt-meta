# Phase 2 Overview: Installable Offline-First PWA Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the installable BioVolt React PWA that consumes the stable Phase 1 REST and `/ws/dashboard` interfaces, renders live scientific telemetry, recent charts, backend/device health, and remains usable offline with clearly labeled cached data.

**Architecture:** The PWA is a read-only scientific presentation layer in Phase 2. FastAPI remains the sole owner of current, power, OD680, biomass, carbon, and cumulative-energy calculations. The frontend receives processed telemetry through `/ws/dashboard`, stores live UI state in Zustand, stores bounded cached telemetry in Dexie/IndexedDB, and uses REST only for status and recent persisted history. The frontend must remain device-source neutral so simulator and real ESP32 telemetry render identically.

**Tech Stack:** React, TypeScript, Vite, Tailwind CSS, Recharts, Zustand, Dexie, IndexedDB, vite-plugin-pwa, React Router, Vitest, React Testing Library, ESLint.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Completed Phase 1 REST surface and processed telemetry WebSocket contract.

## Global Constraints

- Phase 2 must not query SQLite directly.
- Phase 2 must not calculate current, power, OD680, biomass, CO2 biofixed, or cumulative energy.
- The UI displays backend-owned scientific values exactly as received, subject only to presentation formatting.
- The PWA must not branch on simulator device IDs or import simulator code.
- There is no `is_simulated`, `source_type`, or simulator-only UI state.
- `/ws/dashboard` is read-only in Phase 2. No actuator command is sent from the PWA.
- Experiment lifecycle, calibration writes, operator PIN flow, manual actuator control, and A/B experiment workflows are deferred to later phases.
- Backend/device connectivity and browser internet connectivity are tracked separately.
- Cached telemetry must always be labeled cached/stale and must never appear as live data.
- Service worker caches static app assets only. Scientific API responses are not silently served from HTTP cache.
- Live metric cards update at incoming WebSocket cadence, normally approximately 500 ms.
- In-memory live chart buffers are bounded to avoid unbounded browser memory growth.
- Null scientific values render as unavailable, never `0` and never fabricated substitutes.
- PWA must work on the laptop with no external internet connection after its application shell has been installed/cached.
- Production Nginx and Cloudflared routing remain outside Phase 2. Phase 2 may use Vite preview and Compose only for development/integration.

---

## Module Map

### Module 2.1: Frontend Foundation and Application Shell
Plan: `docs/superpowers/plans/phase_2/phase_2_1.md`

Produces:
- Vite + React + TypeScript package
- Tailwind theme and reusable shell
- React Router routes
- sidebar/topbar layout
- testing/lint/typecheck setup

### Module 2.2: Backend Client, Runtime Guards, WebSocket State
Plan: `docs/superpowers/plans/phase_2/phase_2_2.md`

Produces:
- typed Phase 1 REST client
- processed-telemetry TypeScript types
- runtime WebSocket payload guard
- reconnecting dashboard WebSocket client
- Zustand telemetry/system store
- source-neutral architecture tests

### Module 2.3: Overview and Live Data Screens
Plan: `docs/superpowers/plans/phase_2/phase_2_3.md`

Produces:
- Overview dashboard
- metric cards
- live device/source selection
- Live Data table
- connection/staleness indicators
- correct null and unit rendering

### Module 2.4: Recent History and Recharts Visualization
Plan: `docs/superpowers/plans/phase_2/phase_2_4.md`

Produces:
- live bounded chart buffer
- recent persisted-history loading
- voltage, current, power, OD680, temperature, lux, cumulative-energy charts
- range/source selection without frontend scientific recalculation

### Module 2.5: Offline PWA, Dexie Cache, Reconnect and Resync
Plan: `docs/superpowers/plans/phase_2/phase_2_5.md`

Produces:
- installable PWA manifest/service worker
- static asset caching
- Dexie telemetry cache
- offline/cached data mode
- reconnect + REST resynchronization
- cache pruning

### Module 2.6: Responsive, Accessible, Failure-Safe UI
Plan: `docs/superpowers/plans/phase_2/phase_2_6.md`

Produces:
- responsive desktop/laptop/mobile layouts
- keyboard/focus semantics
- error boundary
- loading/empty/error/stale states
- bounded render performance
- accessibility/component tests

### Module 2.7: Frontend Integration, Compose, CI, and Acceptance
Plan: `docs/superpowers/plans/phase_2/phase_2_7.md`

Produces:
- frontend Docker image for Vite preview integration
- optional Compose frontend profile
- frontend CI
- backend + simulator + PWA smoke acceptance
- offline installability/manual acceptance checklist

---

## Mandatory Dependency Order

```text
Phase 1 complete
    |
    v
2.1 Frontend foundation
    |
    v
2.2 Backend client + live state
    |
    v
2.3 Overview + Live Data
    |
    v
2.4 Charts + recent history
    |
    v
2.5 PWA offline cache + resync
    |
    v
2.6 Responsive/accessibility/failure states
    |
    v
2.7 Integration + CI + acceptance
    |
    v
Phase 2 complete
```

## Runtime Data Flow

```text
Simulator OR future ESP32
           |
           v
        FastAPI
           |
           +---- GET /api/system/status
           +---- GET /api/telemetry/latest
           +---- GET /api/telemetry/history
           |
           +---- WS /ws/dashboard
                         |
                         v
                DashboardSocketClient
                         |
                         v
                    Zustand store
                     /         \
                    v           v
             React screens    Dexie cache
                    |           |
                    +-----+-----+
                          v
                    Offline fallback
```

The PWA must not know whether the upstream device is simulated or physical.

## Planned Frontend Structure

```text
frontend/
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.ts
├── postcss.config.js
├── eslint.config.js
├── index.html
├── Dockerfile
├── .dockerignore
├── public/
│   ├── biovolt-mark.svg
│   └── icons/
├── src/
│   ├── main.tsx
│   ├── app/
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── ErrorBoundary.tsx
│   ├── components/
│   │   ├── layout/
│   │   ├── metrics/
│   │   ├── status/
│   │   └── charts/
│   ├── pages/
│   │   ├── OverviewPage.tsx
│   │   ├── LiveDataPage.tsx
│   │   ├── ChartsPage.tsx
│   │   └── SystemPage.tsx
│   ├── types/
│   │   ├── telemetry.ts
│   │   └── system.ts
│   ├── lib/
│   │   ├── api.ts
│   │   ├── dashboardSocket.ts
│   │   ├── format.ts
│   │   └── stale.ts
│   ├── stores/
│   │   └── telemetryStore.ts
│   ├── hooks/
│   │   ├── useDashboardSocket.ts
│   │   └── useSystemStatus.ts
│   ├── db/
│   │   ├── appDb.ts
│   │   └── telemetryCache.ts
│   ├── pwa/
│   │   └── registerPwa.ts
│   └── styles/
│       └── index.css
└── tests/
    ├── app/
    ├── components/
    ├── lib/
    ├── stores/
    ├── db/
    └── integration/
```

## Phase 2 Route Surface

```text
/          Overview
/live      Live Data
/charts    Charts
/system    System Status
```

Do not create non-functional experiment, control, or calibration routes in Phase 2. They are added only when their backend workflows exist.

## Live-State Rules

- Key telemetry by `(device_id, cell_id)`.
- First valid live source may become the selected source when no user selection exists.
- User selection persists locally.
- A source is visually stale when latest valid telemetry age exceeds 3 seconds.
- WebSocket disconnected is distinct from device stale.
- Latest values remain visible during brief reconnects but receive a stale/disconnected label.
- Live buffer cap: 1,200 frames per source, approximately 10 minutes at 2 Hz.
- Dexie cache writes are throttled to approximately 1 Hz per source.

## Planned Commit Sequence

1. `chore: bootstrap BioVolt React PWA`
2. `feat: connect PWA to BioVolt backend telemetry`
3. `feat: add overview and live telemetry screens`
4. `feat: add BioVolt telemetry charts and history`
5. `feat: add offline PWA cache and reconnect recovery`
6. `feat: harden responsive accessible dashboard states`
7. `test: add frontend integration CI and acceptance checks`

Each commit must pass all tests introduced up to that point.

## Phase 2 Exit Criteria

- [ ] Frontend builds with TypeScript strict checks and linting.
- [ ] `/ws/dashboard` processed telemetry reaches the Zustand store.
- [ ] Invalid WebSocket payloads are rejected without crashing the app.
- [ ] UI does not calculate backend-owned scientific values.
- [ ] UI contains no simulator-specific dependency or device-ID branching.
- [ ] Overview shows voltage, current, power, OD680, temperature, lux, cumulative energy, actuator state, mode, and freshness when values are available.
- [ ] Null values render as unavailable rather than zero.
- [ ] Live Data screen shows the exact latest backend telemetry fields with units.
- [ ] Charts render bounded live data without unbounded memory growth.
- [ ] Recent persisted history can be loaded from Phase 1 REST endpoint.
- [ ] Backend disconnect visibly changes connection state.
- [ ] Device stale condition is distinct from browser/network offline condition.
- [ ] Installed/cached app shell opens without external internet.
- [ ] Offline mode shows last cached data with explicit cached timestamp/state.
- [ ] Service worker does not silently cache scientific REST responses.
- [ ] Reconnection triggers status/latest/history resynchronization.
- [ ] Desktop/laptop/mobile layouts remain usable.
- [ ] Keyboard focus, semantic labels, and status announcements are tested.
- [ ] Backend + simulator + PWA integration smoke passes.
- [ ] Frontend CI passes tests, typecheck, lint, and production build.
- [ ] No experiment write APIs, actuator commands, calibration writes, Nginx, or Cloudflared production routing have entered Phase 2.

## Handoff to Phase 3

Phase 3 implements the real ESP32 firmware against the already-stable `device-telemetry.v1` and `/ws/device` boundary. The Phase 2 PWA must require no changes merely because the upstream telemetry source changes from simulator to ESP32.
