# Phase 8.4: Deployment Resilience, Security, and Operations Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the production BioVolt stack starts predictably, survives expected venue/network/container failures, preserves experiment data, and enforces the public security boundary.

**Architecture:** Acceptance is performed against the production Compose topology, not development servers. Automated scripts cover repeatable service/security checks, while an operator runbook covers hardware/network interruptions that cannot be reproduced reliably in CI.

**Tech Stack:** Docker Compose, Nginx, FastAPI, SQLite, pytest/scripts, shell/PowerShell-compatible runbooks.

**Spec:** `docs/superpowers/plans/phase_8/phase_8_0.md`

## Global Constraints
- Local operation must work with internet disconnected.
- Data persistence must survive container recreation.
- Cloudflared failure must be isolated from the local system.
- Public routes must remain read-only under adversarial request attempts.
- Recovery procedures must be executable by the team during a hackathon without editing source code.

---

### Task 1: Production cold-start acceptance script

**Files:**
- Create: `scripts/phase8_cold_start.py`
- Create: `docs/deployment/cold-start.md`

- [ ] Define preconditions: Docker available, `.env` prepared, no required internet.
- [ ] Start from stopped containers with `docker compose up -d`.
- [ ] Poll Nginx local route, FastAPI health, SQLite readiness, dashboard WebSocket readiness.
- [ ] Require all mandatory services healthy within a documented timeout.
- [ ] Verify simulator is absent unless its profile is explicitly enabled.
- [ ] Stop and rerun the procedure from a clean process state.
- [ ] Commit `test: add BioVolt production cold-start acceptance`.

### Task 2: Persistence and backup acceptance

**Files:**
- Create: `scripts/phase8_persistence.py`
- Create: `scripts/backup_biovolt.py`
- Create: `docs/deployment/backup-restore.md`

- [ ] Seed a clearly synthetic test experiment in an isolated acceptance environment.
- [ ] Record row counts and identifiers before container restart/recreation.
- [ ] Recreate backend/Nginx containers without deleting the persistent volume.
- [ ] Verify experiment, telemetry, calibration revision, and analytics rows remain intact.
- [ ] Implement a backup command that safely copies SQLite using the SQLite backup API or equivalent consistent snapshot method rather than copying a live database unsafely.
- [ ] Document restore verification into a separate acceptance database.
- [ ] Commit `test: validate BioVolt persistence and backup`.

### Task 3: Offline venue and Cloudflared-isolation drill

**Files:**
- Create: `docs/deployment/offline-drill.md`
- Create: `scripts/phase8_offline_check.py`

- [ ] With production stack healthy, disconnect upstream internet while keeping laptop hotspot/LAN active.
- [ ] Verify local PWA loads or continues from installed/cached shell as designed.
- [ ] Verify ESP32 telemetry reaches `/ws/device` locally.
- [ ] Verify experiment persistence and operator controls remain functional.
- [ ] Restore internet and verify optional Cloudflared recovers independently.
- [ ] Stop/kill Cloudflared explicitly and prove no local service restarts or degrades.
- [ ] Commit `test: verify BioVolt offline venue operation`.

### Task 4: Public penetration matrix

**Files:**
- Create: `scripts/phase8_public_penetration.py`
- Create: `docs/deployment/public-security-matrix.md`

- [ ] Enumerate every known API/WebSocket route by method and expected public behavior.
- [ ] Test safe GETs for expected access.
- [ ] Test POST/PATCH/PUT/DELETE writes and require 403/404.
- [ ] Test operator login/logout publicly and require denial.
- [ ] Test `/ws/device` publicly and require denial.
- [ ] Test spoofed trusted headers and require no privilege elevation.
- [ ] Test path-normalization variants/trailing slashes for blocked routes.
- [ ] Store the matrix in CI-readable form and fail when a new route is unclassified.
- [ ] Commit `test: add BioVolt public penetration matrix`.

### Task 5: Restart and degraded-service recovery

**Files:**
- Create: `scripts/phase8_restart_matrix.py`
- Modify: `docs/deployment/operations.md`

- [ ] Restart backend alone and verify Nginx remains up and PWA reports backend disconnected rather than crashing.
- [ ] Verify ESP32 reconnects after backend returns.
- [ ] Restart Nginx alone and verify backend/data remain intact.
- [ ] Restart the complete Compose stack and verify automatic recovery.
- [ ] Verify stale-data banners clear only after genuinely fresh telemetry arrives.
- [ ] Verify an interrupted control request is not replayed automatically.
- [ ] Commit `test: validate BioVolt production restart recovery`.

### Task 6: Phase 8 regression gate

**Files:**
- Create: `scripts/phase8_acceptance.py`
- Modify: `.github/workflows/integration.yml`

- [ ] Aggregate cold-start, public-boundary, persistence, PWA production build, backend tests, frontend tests, and firmware/native tests where CI-compatible.
- [ ] Keep physical hotspot/internet drills documented as required manual gates.
- [ ] Print a concise pass/fail report with no ambiguous warnings counted as passes.
- [ ] Verify all Phase 0-7 automated regressions remain green.
- [ ] Commit `test: add Phase 8 production acceptance gate`.

## Exit Criteria
- [ ] One-command local production startup is verified.
- [ ] No internet dependency exists for core operation.
- [ ] Persistent scientific/experiment data survives service recreation.
- [ ] Backup and restore procedure is tested.
- [ ] Public security matrix is fail-closed and complete.
- [ ] Cloudflared failure is isolated.
- [ ] Backend/Nginx/full-stack restart recovery is verified.
- [ ] No failed control write is automatically replayed.
- [ ] Phase 0-7 regressions remain green.
