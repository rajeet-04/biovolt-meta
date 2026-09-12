# Phase 8 Overview: Production Packaging and Read-Only Judge Access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package BioVolt into a one-command offline-first production deployment and add an optional HTTPS read-only judge surface that cannot reach hardware control, calibration writes, experiment writes, or the device WebSocket.

**Architecture:** A production Nginx container serves the built React PWA and proxies same-origin API/WebSocket traffic to an internal FastAPI container. SQLite and CSV data live on a persistent backend volume. Nginx exposes two deliberately different access surfaces: a full local operator listener and a restricted read-only listener. Optional Cloudflared connects only to the restricted listener. Local operation and ESP32 communication never depend on Cloudflared or internet connectivity.

**Tech Stack:** Docker Compose, Nginx, FastAPI/Uvicorn, React/Vite production build, SQLite persistent volume, optional Cloudflared.

**Spec:** `docs/architecture/software-architecture.md`

**Depends on:** Phase 7 analytics/reporting and all Phase 0 to 6 device/control/calibration behavior.

## Global Constraints

- `docker compose up -d` launches the complete local operator stack without Cloudflared.
- Cloudflared is an optional Compose profile only.
- Backend is internal to the Compose network in production and is not directly exposed publicly.
- Nginx is the same-origin entry point for `/`, `/api/*`, `/ws/device`, and `/ws/dashboard` on the local operator listener.
- Public/read-only listener must not proxy `/ws/device`.
- Public/read-only listener must reject every state-changing API route, regardless of whether frontend controls are hidden.
- Public/read-only listener must reject operator login/session writes.
- Public judge access may view safe live dashboard data, completed experiment results, quality/provenance, and safe exports.
- Local operator access retains full authenticated experiment/control/calibration workflow.
- ESP32 connects over the laptop hotspot/LAN to the local operator listener or a dedicated local device route, never through Cloudflared.
- Venue internet failure must not affect ESP32 sensing/control, backend persistence, local PWA, or local experiment operation.
- Secrets live in `.env`/Compose secrets or local configuration and are never committed.
- Production deployment does not add Redis, MQTT, PostgreSQL, or another database container.
- Existing evidence-class semantics remain visible in deployment UI.

---

## Target Production Topology

```text
ESP32 on laptop hotspot
        |
        | ws://laptop-local-address/ws/device
        v
+------------------------------------------------+
|                Nginx container                 |
|                                                |
| local operator listener :80                    |
|   /                   -> React PWA             |
|   /api/*              -> FastAPI               |
|   /ws/device          -> FastAPI               |
|   /ws/dashboard       -> FastAPI               |
|                                                |
| read-only listener :8081                       |
|   /                   -> same React PWA        |
|   safe GET /api/*     -> FastAPI               |
|   /ws/dashboard       -> FastAPI               |
|   writes/device WS    -> 403/404               |
+---------------------+--------------------------+
                      |
                      v
               FastAPI container
                      |
                      v
          persistent /data volume
          SQLite + CSV/exports

Optional internet path:
Cloudflared profile -> Nginx read-only :8081 only
```

The precise host ports may be configurable, but the local/public security boundary must remain structurally separate.

---

## Access Modes

Backend/PWA expose a simple capability contract:

```text
access_mode = operator | public_read_only
can_control = boolean
can_manage_experiments = boolean
can_manage_calibration = boolean
can_view_live = boolean
can_export = boolean
```

A proposed route:

```text
GET /api/capabilities
```

The result is determined from trusted reverse-proxy context, not an arbitrary query parameter supplied by the browser.

Local listener adds an internal trusted header such as:

```text
X-BioVolt-Access-Mode: operator
```

Read-only listener adds:

```text
X-BioVolt-Access-Mode: public_read_only
```

FastAPI validates only expected values from the private proxy network. Nginx itself remains the primary method-level/path-level public write barrier.

---

## Public Route Policy

Allowed public examples:

```text
GET /api/health
GET /api/system/status
GET /api/capabilities
GET /api/telemetry/latest...
GET /api/telemetry/history...
GET /api/experiments
GET /api/experiments/{id}
GET /api/experiments/{id}/analytics/*
GET /api/calibration/profiles/{id} or safe revision reads when needed for provenance
GET analytics/export.csv when classified safe
WS  /ws/dashboard
```

Blocked public examples:

```text
/ws/device
POST /api/operator/login
POST /api/operator/logout
POST/PATCH/DELETE experiment mutation routes
POST /api/control/*
POST /api/calibration/* write/capture/activate routes
any future method that changes hardware, experiment state, calibration, or auth state
```

Use an allow-list approach for the read-only listener where practical. A new write route should fail closed until explicitly reviewed.

---

## PWA/Secure-Context Rules

- `http://localhost` is acceptable for local PWA/service-worker development and installation on the laptop.
- Raw LAN HTTP addresses may not provide the same secure-context/install behavior in every browser.
- The team should preinstall/test the PWA locally before the event.
- Optional Cloudflared gives an HTTPS judge URL when internet is available.
- PWA installability is not a dependency for core local browser operation.
- Service worker must never cache POST/control requests for replay.

---

## Module Map

### Module 8.1: Production Frontend, Nginx, and Compose Stack
Plan: `docs/superpowers/plans/phase_8/phase_8_1.md`

Produces:
- production frontend multi-stage image
- Nginx SPA/static serving
- same-origin API/WebSocket proxy
- persistent backend volume
- healthchecks/restart policy
- one-command local startup
- dev/production Compose separation

### Module 8.2: Read-Only Public Boundary and Optional Cloudflared
Plan: `docs/superpowers/plans/phase_8/phase_8_2.md`

Produces:
- public read-only Nginx listener
- fail-closed write blocking
- `/api/capabilities`
- trusted access-mode propagation
- optional Cloudflared profile
- public security tests

### Module 8.3: Production PWA Access-Mode, Offline, and Evidence UX
Plan: `docs/superpowers/plans/phase_8/phase_8_3.md`

Produces:
- read-only judge banner
- operator-control hiding/disable behavior
- PWA service-worker production caching rules
- stale/offline/error UX
- synthetic evidence banner persistence
- deployment/runtime config tests

### Module 8.4: Deployment Resilience, Security, and Operations Acceptance
Plan: `docs/superpowers/plans/phase_8/phase_8_4.md`

Produces:
- cold-start checklist
- offline venue test
- public write penetration matrix
- restart/volume persistence tests
- backup/export procedure
- Cloudflared failure isolation
- Phase 8 regression gate

---

## Container/Network Model

Recommended services:

```text
nginx
backend
optional simulator profile
optional cloudflared profile
```

No separate frontend runtime server after production build.

Backend Uvicorn is reachable only on the Compose network, e.g. `backend:8000`.

Persistent path:

```text
/data/biovolt.db
/data/exports/
```

Use one named volume or explicitly documented bind mount with backup instructions.

---

## Product Design Requirements

Public judge mode must be self-explanatory:
- persistent `Read-only judge view` indicator
- no misleading enabled-looking buttons that fail only after click
- control/calibration/edit actions are hidden or explicitly unavailable
- live/stale/synthetic evidence states remain visible
- completed Results route is easy to reach from the dashboard
- no login prompt on public route

Local operator mode keeps the full workflows.

The final visual/a11y audit itself is scheduled in Phase 9 after production rendering exists.

## Operational Requirements

One-command local start:

```bash
docker compose up -d
```

Optional public tunnel:

```bash
docker compose --profile public up -d cloudflared
```

A fresh machine still requires documented Docker/runtime prerequisites and environment preparation. Do not claim zero-setup from a completely unprepared laptop.

## Planned Commit Sequence

1. `feat: package BioVolt production stack behind Nginx`
2. `feat: add read-only BioVolt judge access boundary`
3. `feat: adapt BioVolt PWA for production access modes`
4. `test: validate BioVolt deployment resilience and public security`

## Phase 8 Exit Criteria

- [ ] Local stack starts with `docker compose up -d` without internet-dependent service.
- [ ] React assets, REST, and both required WebSockets work through same-origin local Nginx.
- [ ] FastAPI/SQLite data persist across container restart/recreation.
- [ ] ESP32 device socket works locally without Cloudflared.
- [ ] Public listener cannot reach `/ws/device`.
- [ ] Public listener rejects all experiment/control/calibration/auth writes.
- [ ] New public access is fail-closed by default or covered by explicit allow-list tests.
- [ ] PWA visibly distinguishes operator vs read-only judge mode.
- [ ] PWA never queues actuator writes through service worker/offline cache.
- [ ] Cloudflared targets only the read-only listener.
- [ ] Cloudflared/internet failure cannot disrupt local stack.
- [ ] Evidence-class/synthetic labels remain visible in production build.
- [ ] Healthchecks/restart policies are defined and tested.
- [ ] Backup/export procedure for SQLite/experiment CSV is documented.
- [ ] Existing Phase 0 to 7 regression suites remain green.

## Handoff to Phase 9

Phase 9 is the final release-candidate gate. It independently validates hardware measurements and scientific claims, runs cold-start/offline/resilience/soak acceptance, performs the final Product Design audit on production screenshots, validates headline analytics again, and produces the judge demo runbook.
