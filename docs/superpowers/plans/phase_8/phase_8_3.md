# Phase 8.3: Production PWA Access-Mode, Offline, and Evidence UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the production PWA clearly distinguish operator, public read-only, offline, stale, and synthetic-evidence states without allowing cached or hidden controls to create unsafe behavior.

**Architecture:** The PWA reads `/api/capabilities` at startup and treats capabilities as presentation constraints, not security. Service-worker caching is restricted to application shell/static assets and explicitly safe reads, while state-changing requests are always network-only and never queued. Evidence provenance remains visible on every result surface.

**Tech Stack:** React, TypeScript, Zustand, Dexie, vite-plugin-pwa/Workbox, Vitest, Testing Library.

**Spec:** `docs/superpowers/plans/phase_8/phase_8_0.md`

## Global Constraints
- UI hiding is not the security boundary; Nginx/FastAPI enforce access.
- Public mode must be self-explanatory and never show enabled-looking controls that cannot work.
- Cached data must never masquerade as live data.
- Synthetic/demo evidence must stay visibly labeled.
- No service-worker replay of POST/PATCH/DELETE/control traffic.

---

### Task 1: Add typed access-mode state

**Files:**
- Create: `frontend/src/types/capabilities.ts`
- Create: `frontend/src/api/capabilities.ts`
- Modify: `frontend/src/store/systemStore.ts`
- Test: `frontend/src/api/capabilities.test.ts`

**Interfaces:**
- Consumes: `GET /api/capabilities`.
- Produces: typed `Capabilities` state available to routing/layout/components.

- [ ] Write failing runtime-validation tests for operator and public-read-only responses.
- [ ] Implement the TypeScript model matching backend fields exactly.
- [ ] Add startup loading and retry behavior.
- [ ] Treat missing/invalid capabilities as non-elevated until a valid response arrives.
- [ ] Run targeted tests and commit `feat: load BioVolt runtime capabilities in PWA`.

### Task 2: Build operator/public UX boundary

**Files:**
- Create: `frontend/src/components/access/AccessModeBanner.tsx`
- Create: `frontend/src/components/access/CapabilityGate.tsx`
- Modify: app navigation and control/calibration/experiment routes.
- Test: `frontend/src/components/access/CapabilityGate.test.tsx`

- [ ] Write tests proving public mode shows a persistent `Read-only judge view` indicator.
- [ ] Write tests proving control, calibration-edit, experiment-mutation, and login controls are absent or explicitly unavailable in public mode.
- [ ] Keep live telemetry, history, Results, quality/provenance, and approved exports visible.
- [ ] Ensure direct navigation to operator-only screens renders a clear unavailable state rather than broken controls.
- [ ] Keep operator mode unchanged.
- [ ] Commit `feat: adapt BioVolt UI to operator and judge modes`.

### Task 3: Harden production service-worker policy

**Files:**
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/pwa/cachePolicy.ts`
- Test: `frontend/src/pwa/cachePolicy.test.ts`

- [ ] Write failing tests for intended runtime-cache rules.
- [ ] Cache hashed static assets/app shell with revisioning.
- [ ] Make mutation methods network-only and exclude them from background sync.
- [ ] Exclude authentication/control/calibration write endpoints from runtime caches.
- [ ] Keep scientific GET caching explicit, bounded, and timestamp-aware where used.
- [ ] Verify a failed actuator/experiment write is never replayed after reconnection.
- [ ] Commit `fix: harden BioVolt production service-worker policy`.

### Task 4: Implement live, stale, disconnected, and cached-state hierarchy

**Files:**
- Create: `frontend/src/components/status/DataFreshnessBanner.tsx`
- Create: `frontend/src/lib/dataFreshness.ts`
- Modify: Overview, Live Data, Charts, Results screens.
- Test: `frontend/src/lib/dataFreshness.test.ts`

**State priority:**
```text
live
  -> stale
  -> backend_disconnected
  -> cached_offline
  -> no_data
```

- [ ] Define deterministic freshness thresholds from the backend telemetry cadence rather than styling heuristics.
- [ ] Write tests for every state transition.
- [ ] Display the last server timestamp and age when not live.
- [ ] For cached data, show `Showing cached data` and the stored timestamp prominently.
- [ ] Never animate/update cached values as though new telemetry is arriving.
- [ ] Commit `feat: make BioVolt data freshness explicit`.

### Task 5: Preserve evidence provenance in production UX

**Files:**
- Create: `frontend/src/components/evidence/EvidenceBadge.tsx`
- Modify: experiment cards, Results, exports/history UI.
- Test: `frontend/src/components/evidence/EvidenceBadge.test.tsx`

- [ ] Write tests for `measured` and `synthetic_demo` evidence classes.
- [ ] Render synthetic data with an unambiguous `Simulation / demo data` label.
- [ ] Keep measured data unlabeled as simulation but still expose provenance/quality details.
- [ ] Prevent a synthetic experiment comparison from using copy that implies measured hardware improvement.
- [ ] Verify labels remain visible in public read-only mode and offline cached results.
- [ ] Commit `feat: preserve BioVolt evidence provenance in production UI`.

### Task 6: Product interaction acceptance for production modes

**Files:**
- Create: `frontend/src/__tests__/productionAccessJourney.test.tsx`
- Create: `docs/deployment/operator-vs-public-ux.md`

- [ ] Test judge journey: open public URL -> understand read-only mode -> inspect live status -> open Results -> see evidence/quality -> export approved data.
- [ ] Test operator journey: open local URL -> authenticate when required -> create/start experiment -> control allowed mode -> review Results.
- [ ] Test offline transition without page reload and verify stale/cached messaging.
- [ ] Test keyboard navigation through banners/navigation/results and confirm disabled/unavailable actions are announced correctly.
- [ ] Commit `test: validate BioVolt production access-mode UX`.

## Exit Criteria
- [ ] Public mode is unmistakably read-only.
- [ ] No unavailable control looks actionable.
- [ ] Operator mode retains full local workflows.
- [ ] Cached/stale data cannot be confused with live measurements.
- [ ] State-changing requests are never queued/replayed by the service worker.
- [ ] Synthetic/demo provenance remains visible in every relevant production surface.
- [ ] Judge and operator journeys have regression tests.
