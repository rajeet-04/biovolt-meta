# Phase 8.2: Read-Only Public Boundary and Optional Cloudflared Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed public judge surface that exposes safe read-only BioVolt data while structurally blocking all device, auth, experiment, control, and calibration writes.

**Architecture:** Nginx exposes a separate read-only listener that uses an explicit allow-list and injects a trusted access-mode header to FastAPI. FastAPI exposes `/api/capabilities` and independently rejects public-write requests as defense in depth. Cloudflared, when enabled, targets only the read-only listener.

**Tech Stack:** Nginx, FastAPI, Docker Compose, pytest/httpx, WebSocket integration tests, optional Cloudflared.

**Spec:** `docs/superpowers/plans/phase_8/phase_8_0.md`

## Global Constraints
- Public mode is `public_read_only` and local mode is `operator`.
- Browser-controlled query params, cookies, or headers must not be able to elevate public mode.
- `/ws/device` is never exposed through the public listener.
- Public access must fail closed for new write routes.
- Cloudflared is optional and cannot be required by the local operator stack.

---

### Task 1: Define access-mode capability model

**Files:**
- Create: `backend/app/models/capabilities.py`
- Create: `backend/app/services/access_mode.py`
- Modify: `backend/app/api/routes/system.py`
- Test: `backend/tests/api/test_capabilities.py`

**Interfaces:**
- Consumes: trusted `X-BioVolt-Access-Mode` value inserted by internal Nginx.
- Produces: `GET /api/capabilities` returning `access_mode`, `can_control`, `can_manage_experiments`, `can_manage_calibration`, `can_view_live`, `can_export`.

- [ ] Write failing tests proving operator mode returns full local capabilities and public mode returns read-only capabilities.
- [ ] Add a test that an unknown/missing untrusted mode resolves to the safest supported behavior for the public listener path, not elevated operator rights.
- [ ] Implement a typed `AccessMode` enum and immutable `Capabilities` response model.
- [ ] Implement access-mode resolution from trusted proxy context only.
- [ ] Run targeted tests and commit `feat: add BioVolt access capability model`.

### Task 2: Add backend defense-in-depth write guard

**Files:**
- Create: `backend/app/security/access_guard.py`
- Modify: experiment/control/calibration/operator mutation routers introduced by Phases 4-6.
- Test: `backend/tests/security/test_public_write_guard.py`

**Interfaces:**
- Consumes: resolved `AccessMode`.
- Produces: dependency/helper that rejects state-changing operations in `public_read_only` with HTTP 403.

- [ ] Write parameterized failing tests for every public mutation family: operator login/logout, experiment create/start/stop/update/delete, control commands, calibration capture/create/activate/update/delete.
- [ ] Implement `require_operator_access()` dependency.
- [ ] Attach it to all mutation routes while leaving safe GETs available.
- [ ] Add regression test proving operator-mode writes remain functional.
- [ ] Commit `feat: block BioVolt writes in public access mode`.

### Task 3: Build read-only Nginx allow-list listener

**Files:**
- Create: `infra/nginx/public-readonly.conf`
- Modify: `infra/nginx/nginx.conf`
- Test: `scripts/test_public_boundary.py`

**Interfaces:**
- Public listener port: internal `8081`.
- Allowed WebSocket: `/ws/dashboard` only.
- Blocked WebSocket: `/ws/device`.

- [ ] Write a boundary test matrix before implementation with expected 2xx/101/403/404 outcomes.
- [ ] Configure safe GET routes explicitly, including health/status/capabilities/telemetry/experiment result reads and approved exports.
- [ ] Configure `/ws/dashboard` WebSocket upgrade proxy.
- [ ] Explicitly reject `/ws/device`.
- [ ] Reject non-GET methods at the public listener unless an individual route is deliberately reviewed later.
- [ ] Inject `X-BioVolt-Access-Mode: public_read_only`, overwriting any client-supplied value.
- [ ] Run the boundary script against Compose and commit `feat: add fail-closed BioVolt public listener`.

### Task 4: Add optional Cloudflared profile

**Files:**
- Create: `infra/cloudflared/config.yml.example`
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Test: `scripts/test_cloudflared_isolation.py`

**Interfaces:**
- Cloudflared origin: `http://nginx:8081` only.
- Local operator listener must not depend on this service.

- [ ] Add failing/static tests that the Cloudflared service points only to the read-only listener.
- [ ] Add optional Compose `public` profile.
- [ ] Document token/tunnel configuration without committing secrets.
- [ ] Verify `docker compose up -d` excludes Cloudflared and succeeds without internet.
- [ ] Verify stopping Cloudflared leaves backend, Nginx, ESP32 local path, and PWA healthy.
- [ ] Commit `feat: add optional read-only Cloudflare tunnel`.

### Task 5: Public-boundary security acceptance

**Files:**
- Create: `scripts/phase8_public_security.py`
- Modify: `docs/deployment/public-access.md`

- [ ] Test every known write endpoint through the public listener and require 403/404.
- [ ] Attempt header spoofing with `X-BioVolt-Access-Mode: operator` and prove Nginx overwrites it.
- [ ] Attempt `/ws/device` connection publicly and require failure.
- [ ] Connect `/ws/dashboard` publicly and require read-only live telemetry.
- [ ] Verify synthetic/measured evidence labels are unchanged through public APIs.
- [ ] Document the allow-list maintenance rule: new write paths are not public until explicitly reviewed.
- [ ] Commit `test: validate BioVolt public read-only boundary`.

## Exit Criteria
- [ ] Public listener exposes only safe reads and dashboard WebSocket.
- [ ] Public clients cannot elevate themselves to operator access.
- [ ] Backend independently rejects public mutations.
- [ ] `/ws/device` is unreachable publicly.
- [ ] Cloudflared targets only read-only Nginx.
- [ ] Local stack remains fully operational without Cloudflared or internet.
