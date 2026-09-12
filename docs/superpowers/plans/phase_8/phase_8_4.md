# Phase 8.4: Deployment Resilience, Security, and Operations Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Apply Ponytail product-design reasoning to every degraded/recovery state exposed to operators or judges. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the production BioVolt stack starts predictably, survives expected venue/network/container failures, preserves experiment data, enforces the public security boundary, and communicates degraded/recovery states clearly enough that the team can recover without source edits.

**Architecture:** Acceptance is performed against the production Compose topology, not development servers. Automated scripts cover repeatable service/security checks. Physical network/hardware drills use an operator runbook. UX acceptance verifies that each technical failure maps to a truthful and actionable visible state.

**Tech Stack:** Docker Compose, Nginx, FastAPI, SQLite, pytest/scripts, browser PWA, shell/PowerShell-compatible runbooks.

**Spec:** `docs/superpowers/plans/phase_8/phase_8_0.md`

## Global Constraints

- Local operation works with upstream internet disconnected.
- Data persistence survives container recreation.
- Cloudflared failure is isolated from the local system.
- Public routes remain read-only under adversarial request attempts.
- Recovery procedures are executable during a hackathon without editing source code.
- Failed control writes are never silently replayed.
- PWA failure states reflect actual system state rather than optimistic assumptions.
- A recovery test passes only after fresh telemetry/data confirms recovery.

---

### Task 1: Production cold-start acceptance

**Files:**
- Create: `scripts/phase8_cold_start.py`
- Create: `docs/operations/cold-start.md`
- Create: `docs/operations/pre-demo-checklist.md`

Preconditions:
- Docker/runtime installed
- required production images/dependencies already available if venue internet is absent
- `.env` prepared locally
- persistent volume present or intentionally new
- real ESP32 or explicit simulation profile selected

- [ ] Start from stopped containers with `docker compose up -d`.
- [ ] Poll Nginx, FastAPI health, SQLite readiness, dashboard WebSocket readiness.
- [ ] Require mandatory services healthy within documented timeout.
- [ ] Verify simulator is absent unless explicitly enabled.
- [ ] Verify public/Cloudflared profile is absent during normal local start.
- [ ] Load PWA and verify truthful `waiting for telemetry`/`live` state.
- [ ] Repeat from clean process state.
- [ ] Commit `test: add BioVolt production cold-start acceptance`.

---

### Task 2: Persistence, backup, and restore acceptance

**Files:**
- Create: `scripts/phase8_persistence.py`
- Create: `scripts/backup_biovolt.py`
- Create: `scripts/restore_biovolt_backup.py`
- Create: `docs/operations/backup-restore.md`

- [ ] Seed a clearly synthetic acceptance experiment in an isolated environment.
- [ ] Record experiment/calibration/telemetry/analytics identifiers and counts.
- [ ] Recreate backend/Nginx containers without deleting persistent volume.
- [ ] Verify data remains intact.
- [ ] Implement safe SQLite backup via SQLite backup API or equivalent consistent snapshot method.
- [ ] Restore into a separate acceptance database/volume.
- [ ] Verify restored experiment, calibration provenance, and export integrity.
- [ ] Document `docker compose down -v` as destructive and excluded from normal recovery.
- [ ] Commit `test: validate BioVolt persistence backup and restore`.

---

### Task 3: Offline venue and Cloudflared-isolation drill

**Files:**
- Create: `docs/operations/offline-drill.md`
- Create: `scripts/phase8_offline_check.py`

Drill:

```text
healthy local system
  -> disconnect upstream internet
  -> keep laptop hotspot/LAN active
  -> verify ESP32 + backend + local PWA continue
  -> verify public tunnel becomes unavailable only
  -> restore internet
  -> verify tunnel recovery is independent
```

- [ ] Verify local PWA loads/continues from installed/cached shell as designed.
- [ ] Verify ESP32 telemetry continues locally.
- [ ] Verify active experiment persistence/control remains functional.
- [ ] Verify local Results/history remain available.
- [ ] Kill Cloudflared and prove no local container/service restarts because of it.
- [ ] Verify local operator UI does not show a false system-wide outage just because public tunnel is down.
- [ ] Commit `test: verify BioVolt offline venue operation`.

---

### Task 4: Public penetration matrix

**Files:**
- Create: `scripts/phase8_public_penetration.py`
- Create: `docs/operations/public-security-matrix.md`

- [ ] Enumerate every known API/WebSocket route and classify public behavior.
- [ ] Test safe GETs.
- [ ] Test POST/PATCH/PUT/DELETE writes and require 403/404.
- [ ] Test operator login/logout publicly and require denial.
- [ ] Test `/ws/device` publicly and require denial.
- [ ] Test spoofed trusted headers.
- [ ] Test trailing slashes/path normalization variants where relevant.
- [ ] Record pre/post DB and actuator state to prove no mutation.
- [ ] Fail when a new route is unclassified.
- [ ] Commit `test: add BioVolt public penetration matrix`.

---

### Task 5: Restart and degraded-service recovery matrix

**Files:**
- Create: `scripts/phase8_restart_matrix.py`
- Modify: `docs/operations/operations.md`

Scenarios:

```text
backend restart
nginx restart
full Compose restart
browser refresh during outage
ESP32 reconnect after backend restart
upstream internet loss
Cloudflared process death
```

For each scenario verify both **technical recovery** and **visible-state recovery**.

- [ ] Restart backend; Nginx/PWA stay up and show backend disconnected/stale, not false live.
- [ ] Verify ESP32 reconnects after backend returns.
- [ ] Restart Nginx; backend/data remain intact.
- [ ] Restart full Compose stack; data persist and PWA recovers.
- [ ] Clear stale state only after fresh telemetry arrives.
- [ ] Verify interrupted write is not replayed automatically.
- [ ] Commit `test: validate BioVolt production restart recovery`.

---

### Task 6: Ponytail degraded-state and recovery experience audit

**Files:**
- Create: `docs/product/recovery-state-audit.md`
- Create: `docs/product/operator-recovery-card.md`

Audit every important degraded state:

| Technical condition | Required visible state | Primary operator action |
|---|---|---|
| backend unavailable | Backend disconnected | Wait/restart backend using runbook |
| telemetry older than threshold | Stale data | Check device/network; do not imply live |
| internet/Cloudflared down only | Public link unavailable | Continue local operation |
| cached PWA only | Showing cached data | Reconnect; no control writes |
| ESP32 disconnected | Device disconnected | Check hotspot/power/device |
| sensor invalid | Sensor unavailable | Inspect sensor/connection |
| comparison quality failed | Unavailable + reason | Inspect quality/provenance |

Product requirements:
- one dominant recovery message per condition, not multiple conflicting alerts
- action copy says what the operator can actually do
- no raw stack trace in judge/operator primary view
- technical diagnostics remain accessible separately for the team
- recovery success is visible only after a real healthy signal

- [ ] Walk through each condition in production UI.
- [ ] Capture screenshots for Phase 9 audit.
- [ ] Document any confusing copy/hierarchy as MAJOR before release.
- [ ] Commit `docs: define Ponytail BioVolt recovery-state audit`.

---

### Task 7: Performance/resource sanity under production load

**Files:**
- Create: `scripts/phase8_resource_sanity.py`
- Create: `docs/operations/resource-baseline.md`

Measure during a representative run:
- backend process/container memory
- SQLite file growth rate
- browser live-buffer size
- WebSocket reconnect count
- Nginx/backend CPU sanity
- ESP32 free heap from existing status telemetry/runbook

This is not a cloud-scale benchmark. It is a hackathon reliability guard against obvious leaks/unbounded buffers.

- [ ] Run at least 30 minutes with live/simulated telemetry.
- [ ] Verify frontend bounded buffers remain bounded.
- [ ] Verify backend/database growth matches intended persistence cadence.
- [ ] Record baseline for Phase 9 soak comparison.
- [ ] Commit `test: baseline BioVolt production resource usage`.

---

### Task 8: Phase 8 regression gate

**Files:**
- Create: `scripts/phase8_acceptance.py`
- Modify: `.github/workflows/integration.yml`
- Create: `docs/operations/phase8-acceptance.md`

Automated aggregate:
- Phase 0 schemas/contracts
- backend tests
- frontend tests/build
- firmware native/build tests
- production Compose config/build
- production route smoke
- public penetration matrix
- persistence/backup verification where CI-compatible

Manual required gates:
- actual upstream-internet loss
- actual laptop-hotspot continuity
- hardware/device reconnect
- production UI recovery screenshots

- [ ] Print concise pass/fail summary.
- [ ] Warnings do not count as passes for mandatory gates.
- [ ] Verify all Phase 0-7 automated regressions remain green.
- [ ] Commit `test: add Phase 8 production acceptance gate`.

## Module 8.4 Exit Criteria

- [ ] One-command local production startup is verified.
- [ ] Core operation has no upstream-internet dependency.
- [ ] Persistent scientific data survives service recreation.
- [ ] Backup and restore are tested.
- [ ] Public security matrix is fail-closed and complete.
- [ ] Cloudflared failure is isolated.
- [ ] Backend/Nginx/full-stack restart recovery is verified.
- [ ] No failed write is automatically replayed.
- [ ] Visible degraded/recovery states match technical truth.
- [ ] Resource sanity shows no obvious unbounded growth.
- [ ] Phase 0-7 regressions remain green.
