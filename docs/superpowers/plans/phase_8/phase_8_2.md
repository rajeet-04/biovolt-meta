# Phase 8.2: Read-Only Public Boundary and Optional Cloudflared Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Apply Ponytail product-design reasoning to every public-access state and judge-facing transition. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed public judge surface that exposes safe read-only BioVolt data while structurally blocking all device, auth, experiment, control, and calibration writes.

**Architecture:** Nginx exposes a separate read-only listener that uses an explicit allow-list and injects a trusted access-mode header to FastAPI. FastAPI exposes `/api/capabilities` and independently rejects public-write requests as defense in depth. Cloudflared, when enabled, targets only the read-only listener. The browser may adapt presentation from capabilities, but it is never the security boundary.

**Tech Stack:** Nginx, FastAPI, Docker Compose, pytest/httpx, WebSocket integration tests, optional Cloudflared.

**Spec:** `docs/superpowers/plans/phase_8/phase_8_0.md`

## Global Constraints

- Public mode is `public_read_only`; local mode is `operator`.
- Browser-controlled query params, cookies, local storage, or headers cannot elevate public mode.
- `/ws/device` is never exposed through the public listener.
- Public access must fail closed for new write routes.
- Cloudflared is optional and cannot be required by the local operator stack.
- Public exports are generated safe artifacts, never raw database downloads.
- Public mode shows no operator login prompt and no action that appears executable but is guaranteed to fail.
- Synthetic/demo evidence remains unmistakably different from measured evidence.

---

## Public Route Policy Contract

Initial safe-read allow-list should be derived from the actual Phase 4 to 7 route names. Expected categories:

```text
GET /api/health
GET /api/system/status
GET /api/capabilities
GET /api/telemetry/latest
GET /api/telemetry/history
GET /api/experiments
GET /api/experiments/{id}
GET /api/experiments/{id}/analytics/*
GET /api/experiments/{id}/export.csv
GET safe calibration provenance reads
WS  /ws/dashboard
```

Explicit public denies:

```text
/ws/device
POST /api/operator/login
POST /api/operator/logout
all experiment mutation routes
all control mutation routes
all calibration capture/create/activate/update/delete routes
all future state-changing routes until reviewed
```

If implementation route names differ, update this allow-list to match the actual routes. Do not create duplicate endpoints merely to satisfy this document.

---

### Task 1: Define trusted access-mode capability model

**Files:**
- Create: `backend/src/biovolt_backend/models/capabilities.py`
- Create: `backend/src/biovolt_backend/services/access_mode.py`
- Create or Modify: `backend/src/biovolt_backend/api/system.py`
- Test: `backend/tests/api/test_capabilities.py`
- Test: `backend/tests/test_access_mode.py`

**Interfaces:**
- Consumes: trusted `X-BioVolt-Access-Mode` inserted/overwritten by internal Nginx.
- Produces: `GET /api/capabilities`.

Expected public response:

```json
{
  "access_mode": "public_read_only",
  "can_control": false,
  "can_manage_experiments": false,
  "can_manage_calibration": false,
  "can_view_live": true,
  "can_export": true
}
```

Rules:
- only known enum values are accepted internally
- browser-supplied mode is never authoritative
- direct backend development mode uses explicit configuration, not request parameters
- access mode and Phase 4 operator authentication remain separate concerns

- [ ] Write failing tests for operator/public capability responses.
- [ ] Write failing test for unknown/invalid access mode.
- [ ] Implement typed immutable `AccessMode` and `Capabilities` models.
- [ ] Implement access-mode resolution.
- [ ] Add `/api/capabilities`.
- [ ] Verify no token, PIN state, tunnel secret, or Wi-Fi data appears in capability output.
- [ ] Commit `feat: add BioVolt trusted access capabilities`.

---

### Task 2: Add backend defense-in-depth public-write guard

**Files:**
- Create: `backend/src/biovolt_backend/security/public_write_guard.py`
- Modify: Phase 4 experiment/control mutation routers.
- Modify: Phase 5 calibration mutation routers.
- Test: `backend/tests/security/test_public_write_guard.py`

Expected behavior:

```text
public_read_only + mutation -> 403
operator + valid operator session -> route proceeds
operator + invalid session -> existing Phase 4 auth failure
```

- [ ] Write parameterized failing tests for operator-auth, experiment, control, and calibration mutation families.
- [ ] Implement one reusable `require_operator_access()` dependency/policy.
- [ ] Attach at router/dependency boundaries, not ad hoc inside components.
- [ ] Verify safe reads remain available.
- [ ] Commit `feat: reject public BioVolt writes in backend`.

---

### Task 3: Build structurally separate public Nginx listener

**Files:**
- Create: `deploy/nginx/conf.d/public-read-only.conf`
- Modify: `deploy/nginx/nginx.conf`
- Create: `docs/operations/public-route-policy.md`
- Test: `scripts/verify_public_route_policy.py`

Recommended internal listeners:

```text
:80   operator
:8081 public_read_only
```

Public listener requirements:
- same PWA assets
- `/ws/dashboard` upgrade permitted
- `/ws/device` explicitly denied
- safe GET allow-list only
- state-changing HTTP methods rejected
- inject `X-BioVolt-Access-Mode: public_read_only`
- overwrite any client-supplied access-mode header

Operator listener requirements:
- inject/overwrite `X-BioVolt-Access-Mode: operator`
- retain `/ws/device` and operator APIs

- [ ] Write route/method matrix before Nginx implementation.
- [ ] Configure explicit safe-read locations.
- [ ] Explicitly deny `/ws/device`.
- [ ] Deny mutation methods/paths.
- [ ] Verify header spoofing does not elevate capability response.
- [ ] Document every allowed public category and rationale.
- [ ] Commit `feat: isolate BioVolt read-only public listener`.

---

### Task 4: Add optional Cloudflared profile

**Files:**
- Modify: `docker-compose.yml`
- Create: `deploy/cloudflared/README.md`
- Create: `.env.public.example`
- Modify: `.gitignore`
- Test: `scripts/verify_cloudflared_target.sh`

Cloudflared rules:

```text
Compose profile: public
origin: http://nginx:8081 only
local stack has no dependency on cloudflared
```

- [ ] Add profile without changing normal `docker compose up -d` behavior.
- [ ] Verify origin is exactly the read-only listener.
- [ ] Verify token/credential placeholders only are committed.
- [ ] Kill Cloudflared and prove local sensing, experiments, backend, and PWA remain healthy.
- [ ] Document tunnel startup/shutdown.
- [ ] Commit `feat: add optional read-only BioVolt Cloudflared profile`.

---

### Task 5: Build exhaustive public penetration matrix

**Files:**
- Create: `scripts/public_security_matrix.py`
- Create: `backend/tests/integration/test_public_surface.py`
- Modify: `docs/operations/public-route-policy.md`

Matrix dimensions:

```text
method: GET/POST/PUT/PATCH/DELETE
route family:
  status/capabilities
  telemetry
  experiment reads
  analytics/export
  experiment mutation
  control
  calibration read
  calibration mutation
  operator auth
websocket:
  dashboard
  device
spoofing:
  no header
  client sends operator header
path variants:
  trailing slash
  normalized/encoded variants where relevant
```

Required assertions:
- safe reads work
- writes fail before state mutation
- `/ws/device` never upgrades publicly
- `/ws/dashboard` upgrades read-only
- spoofed mode does not change capabilities
- actuator state and DB state are unchanged after penetration attempts

- [ ] Capture pre-test DB/control state.
- [ ] Run full matrix.
- [ ] Capture post-test state and prove no mutation.
- [ ] Fail CI when a new route is unclassified.
- [ ] Commit `test: enforce BioVolt public read-only security matrix`.

---

### Task 6: Ponytail judge-entry product-design gate

**Files:**
- Create: `docs/product/judge-access-journey.md`
- Create: `docs/product/judge-access-state-matrix.md`

Primary judge journey:

```text
Open HTTPS judge URL
    ↓
Understand "Read-only judge view" immediately
    ↓
See live/stale/offline + evidence provenance
    ↓
Open completed Results
    ↓
Understand primary outcome and eligibility
    ↓
Inspect supporting chart / safe export
```

Define state matrix for:
- healthy live measured system
- healthy live simulator/demo system
- stale telemetry
- backend disconnected
- internet tunnel down while local system healthy
- no completed experiment
- comparison ineligible because quality/provenance requirements fail

Product acceptance:
- no login prompt publicly
- no enabled-looking control/edit affordances
- read-only indicator persists but does not dominate the scientific result
- `Simulation / demo data` is visually explicit
- `Unavailable` includes a reason when a headline scientific comparison is ineligible
- Results is reachable in one obvious navigation action from Overview
- mobile and desktop hierarchy preserve the same meaning

- [ ] Document jobs-to-be-done and state matrix.
- [ ] Define screenshot acceptance set for desktop and mobile.
- [ ] Define copy for read-only, stale, offline, simulation, and unavailable states.
- [ ] Commit `docs: define Ponytail BioVolt judge-access journey`.

## Module 8.2 Exit Criteria

- [ ] Public/operator listeners are structurally separate.
- [ ] Public routes are fail-closed.
- [ ] Public clients cannot elevate themselves to operator.
- [ ] Backend independently rejects public mutations.
- [ ] `/ws/device` is unreachable publicly.
- [ ] Cloudflared reaches only the read-only listener.
- [ ] Local operation is unaffected by internet/Cloudflared loss.
- [ ] Penetration matrix proves no DB/actuator mutation.
- [ ] Judge entry states and product hierarchy are specified before UI work.
