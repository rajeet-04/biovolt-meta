# Phase 8.3: Production PWA Access-Mode, Offline, and Evidence UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Apply Ponytail product-design reasoning to hierarchy, state transitions, copy, accessibility, and judge/operator journeys. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the production PWA clearly distinguish operator, public read-only, offline, stale, disconnected, unavailable, and synthetic-evidence states without allowing cached or hidden controls to create unsafe behavior.

**Architecture:** The PWA reads `/api/capabilities` at startup and treats capabilities as presentation constraints, not security. Service-worker caching is restricted to application shell/static assets plus explicitly safe timestamp-aware reads. State-changing requests are always network-only and never queued. Evidence provenance and data freshness remain visible on every scientific result surface.

**Tech Stack:** React, TypeScript, Zustand, Dexie, vite-plugin-pwa/Workbox, Vitest, Testing Library.

**Spec:** `docs/superpowers/plans/phase_8/phase_8_0.md`

## Global Constraints

- UI hiding is not the security boundary; Nginx/FastAPI enforce access.
- Public mode is self-explanatory and never shows enabled-looking controls that cannot work.
- Cached data never masquerades as live data.
- Synthetic/demo evidence stays visibly labeled.
- No service-worker replay of POST/PUT/PATCH/DELETE/control traffic.
- Scientific `Unavailable` values show a reason when one is known.
- Freshness/provenance states are communicated with text/iconography, not color alone.
- Accessibility and mobile layouts preserve meaning, not just visual resemblance.

---

### Task 1: Add typed runtime access-mode state

**Files:**
- Create: `frontend/src/types/capabilities.ts`
- Create: `frontend/src/api/capabilities.ts`
- Modify: `frontend/src/store/systemStore.ts`
- Test: `frontend/src/api/capabilities.test.ts`

**Interfaces:**
- Consumes: `GET /api/capabilities`.
- Produces: typed capabilities used by routing/layout/components.

- [ ] Write failing runtime-validation tests for operator and `public_read_only` responses.
- [ ] Implement TypeScript model matching backend fields exactly.
- [ ] Add startup loading/retry state.
- [ ] Treat missing/invalid capabilities as non-elevated until a valid response arrives.
- [ ] Ensure cached capabilities never grant operator mutation rights after reconnect/context change.
- [ ] Commit `feat: load BioVolt runtime capabilities in PWA`.

---

### Task 2: Build operator/public product boundary

**Files:**
- Create: `frontend/src/components/access/AccessModeBanner.tsx`
- Create: `frontend/src/components/access/CapabilityGate.tsx`
- Create: `frontend/src/components/access/UnavailableAction.tsx`
- Modify: app navigation and control/calibration/experiment routes.
- Test: `frontend/src/components/access/CapabilityGate.test.tsx`

Public-mode behavior:
- persistent `Read-only judge view`
- hide mutation-only navigation where omission improves clarity
- where context matters, render explicit read-only information instead of a disabled form
- no operator login affordance
- no actuator/manual/adaptive/calibration-edit controls
- Results, provenance, telemetry, history, safe export remain accessible

Direct navigation to an operator-only URL must render an explanatory read-only state, not a blank page or a form that fails after submission.

- [ ] Write tests for every operator-only route in public mode.
- [ ] Preserve full operator behavior locally.
- [ ] Verify public deep links to Results work without login.
- [ ] Commit `feat: adapt BioVolt UI to operator and judge modes`.

---

### Task 3: Harden production service-worker policy

**Files:**
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/pwa/cachePolicy.ts`
- Test: `frontend/src/pwa/cachePolicy.test.ts`

Allowed caching:
- hashed static assets
- app shell/manifest/icons
- explicitly selected safe GET reads if timestamped and bounded

Forbidden caching/replay:
- auth writes
- experiment writes
- calibration writes
- control commands
- device traffic
- any mutation method

- [ ] Write failing tests for cache classification.
- [ ] Configure static asset precache/revisioning.
- [ ] Keep mutation methods network-only and out of Background Sync.
- [ ] Verify failed control/experiment write is never replayed after reconnection.
- [ ] Verify service-worker update path does not strand an old incompatible app shell indefinitely.
- [ ] Commit `fix: harden BioVolt production service-worker policy`.

---

### Task 4: Implement canonical data-freshness state machine

**Files:**
- Create: `frontend/src/components/status/DataFreshnessBanner.tsx`
- Create: `frontend/src/lib/dataFreshness.ts`
- Modify: Overview, Live Data, Charts, Results screens.
- Test: `frontend/src/lib/dataFreshness.test.ts`

Canonical states:

```text
loading
live
stale
device_disconnected
backend_disconnected
cached_offline
no_data
error
```

Exact decision rules for the hackathon release:

```text
live
  dashboard WebSocket connected
  AND backend reachable
  AND latest valid telemetry age <= 2.0 s

stale
  backend reachable
  AND latest valid telemetry exists
  AND telemetry age > 2.0 s and <= 6.0 s

device_disconnected
  backend reachable
  AND (backend device status is disconnected
       OR latest telemetry age > 6.0 s)

backend_disconnected
  dashboard WebSocket unavailable
  AND backend health/status cannot be reached

cached_offline
  live/backend path unavailable
  AND a timestamped Dexie/IndexedDB cache is intentionally being displayed

no_data
  backend reachable
  AND no telemetry has ever been received for the selected source
```

`error` is reserved for invalid/unhandled response state, not ordinary device/network loss. `loading` exists only until enough information is available to select one of the above states.

- [ ] Write tests for every threshold boundary: exactly 2.0 s, just above 2.0 s, exactly 6.0 s, and just above 6.0 s.
- [ ] Write tests for device-disconnected versus backend-disconnected so those states cannot collapse into one generic offline banner.
- [ ] Show last valid timestamp/age whenever not live and a previous frame exists.
- [ ] Cached state says `Showing cached data` with captured timestamp.
- [ ] Cached numbers remain visually static and are never animated as fresh updates.
- [ ] After reconnect, clear stale/offline/disconnected state only after genuinely fresh telemetry with a newer server timestamp arrives.
- [ ] Commit `feat: make BioVolt data freshness explicit`.

---

### Task 5: Preserve evidence provenance and eligibility

**Files:**
- Create: `frontend/src/components/evidence/EvidenceBadge.tsx`
- Create: `frontend/src/components/evidence/EligibilityNotice.tsx`
- Modify: experiment cards, Results, exports/history UI.
- Test: `frontend/src/components/evidence/EvidenceBadge.test.tsx`

Rules:
- `synthetic_demo` renders `Simulation / demo data`
- measured evidence exposes provenance/quality without simulation wording
- an ineligible comparison never displays a fabricated `0%` or placeholder gain
- `Unavailable` explains the primary reason: insufficient overlap, calibration missing, measured evidence absent, quality gate failed, etc.

- [ ] Test measured/synthetic/ineligible combinations.
- [ ] Verify provenance labels remain visible in public and cached/offline Results.
- [ ] Prevent synthetic comparison copy from implying measured hardware improvement.
- [ ] Commit `feat: preserve BioVolt evidence provenance in production UI`.

---

### Task 6: Ponytail information hierarchy for judge and operator modes

**Files:**
- Create: `docs/product/production-information-hierarchy.md`
- Create: `docs/product/production-copy-contract.md`

Judge hierarchy:

```text
1. What is the system doing now?
2. Is this live/measured/synthetic/stale?
3. What is the primary experiment outcome?
4. Is that outcome scientifically eligible?
5. What evidence supports it?
6. How can I inspect/export it?
```

Operator hierarchy adds:

```text
7. What experiment/mode is active?
8. What control actions are available and safe?
9. What command is pending/acked/rejected?
```

Copy contract must freeze exact user-facing terms for:
- Read-only judge view
- Live
- Stale
- Device disconnected
- Backend disconnected
- Showing cached data
- Simulation / demo data
- Estimated CO2 biofixed into biomass
- Unavailable
- Manual / Passive / Adaptive modes

- [ ] Document hierarchy before visual polish.
- [ ] Define empty/error/recovery copy.
- [ ] Verify no user-facing `PAR` wording remains while BH1750 is the light sensor; use `Light (lux)`.
- [ ] Commit `docs: define Ponytail production information hierarchy`.

---

### Task 7: Responsive and accessibility acceptance

**Files:**
- Create: `frontend/src/__tests__/productionAccessJourney.test.tsx`
- Create: `docs/product/production-accessibility-checklist.md`

Required widths:
- phone portrait
- tablet/small laptop
- primary presentation laptop
- large external display

Acceptance:
- critical status never relies on color alone
- keyboard focus order follows information/action hierarchy
- read-only banner does not cover content
- charts have accessible labels/summary text
- touch targets are usable on mobile
- reduced-motion preference suppresses decorative motion
- focus is restored predictably after dialogs/forms
- destructive/safety-sensitive operator actions use explicit confirmation where Phase 4 specifies it

- [ ] Test judge journey with keyboard only.
- [ ] Test operator journey with keyboard only.
- [ ] Test mobile Results and Overview at narrow width.
- [ ] Run automated accessibility checks available in frontend tooling.
- [ ] Commit `test: validate BioVolt production accessibility and responsive states`.

---

### Task 8: Production journey acceptance

**Files:**
- Create: `docs/product/production-journey-acceptance.md`
- Test: `frontend/src/__tests__/productionJourneys.test.tsx`

Journeys:

**Judge**
```text
open public URL
-> recognize read-only + evidence state
-> inspect live status
-> open Results
-> understand gain/ineligibility
-> inspect supporting chart
-> export safe data
```

**Operator**
```text
open local URL
-> authenticate when needed
-> create/select experiment
-> start Passive/Manual/Adaptive as permitted
-> observe command acknowledgment
-> stop experiment
-> review Results
```

**Recovery**
```text
live
-> backend/network interruption
-> stale/offline/disconnected state
-> no stale write replay
-> reconnect
-> fresh telemetry resumes
-> status returns to live
```

- [ ] Write journey tests around state transitions, not isolated snapshots only.
- [ ] Capture expected production screenshots for Phase 9 visual audit.
- [ ] Commit `test: validate BioVolt production journeys`.

## Module 8.3 Exit Criteria

- [ ] Public mode is unmistakably read-only.
- [ ] No unavailable action looks executable.
- [ ] Operator mode retains local workflows.
- [ ] Cached/stale/device-disconnected/backend-disconnected data cannot be confused with live measurements.
- [ ] Mutation requests are never queued/replayed by service worker.
- [ ] Synthetic/demo provenance remains visible everywhere relevant.
- [ ] Ineligible results render `Unavailable` with reason, not invented metrics.
- [ ] Judge/operator/recovery journeys have regression coverage.
- [ ] Product hierarchy, copy, responsive behavior, and accessibility are documented for Phase 9 audit.
