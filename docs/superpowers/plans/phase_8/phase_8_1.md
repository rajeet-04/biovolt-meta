# Phase 8.1: Production Frontend, Nginx, and Compose Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace development-only service exposure with a reproducible production build where Nginx serves the React PWA, proxies same-origin REST/WebSocket traffic to internal FastAPI, and preserves SQLite/CSV data across container lifecycle.

**Architecture:** A multi-stage frontend image builds static assets and copies them into the Nginx image. FastAPI runs as a separate internal service. Nginx is the only normal browser/device-facing service in the production Compose file. Development Compose overrides may continue exposing Vite/FastAPI directly for developer convenience but must not alter production assumptions.

**Tech Stack:** Docker, Docker Compose, Nginx, Node/Vite build, FastAPI/Uvicorn, SQLite named volume.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Local production launch works without internet after images/dependencies are already present on the laptop.
- Backend data directory is persistent.
- Nginx supports WebSocket upgrade headers for `/ws/device` and `/ws/dashboard`.
- SPA routes fall back to `index.html` without swallowing `/api` or `/ws` paths.
- Browser API/WebSocket traffic uses same origin, eliminating production CORS dependency.
- Backend does not bind a public host port in the production Compose definition unless a documented local-debug override explicitly adds one.
- Frontend build contains no device/operator secret.
- Healthcheck failure should restart service under documented restart policy.

---

### Task 1: Add production frontend/Nginx image

**Files:**
- Create: `frontend/Dockerfile`
- Create: `deploy/nginx/nginx.conf`
- Create: `deploy/nginx/conf.d/operator.conf`
- Modify: `frontend/.dockerignore` or root `.dockerignore` as appropriate
- Test: `scripts/test_production_nginx.sh`

Multi-stage image:

```text
node build stage
  npm ci
  npm run build
        |
        v
nginx runtime stage
  copy dist -> /usr/share/nginx/html
  copy config
```

Operator listener routing:

```text
/                 static/PWA with SPA fallback
/api/             proxy_pass http://backend:8000
/ws/device        websocket proxy to backend
/ws/dashboard     websocket proxy to backend
```

- [ ] **Step 1: Write smoke script expectations before Dockerfile**

Expected after stack starts:

```bash
curl -f http://localhost/api/health
curl -f http://localhost/
```

and a WebSocket-capable integration check for dashboard/device route performed in later task.

- [ ] **Step 2: Implement multi-stage frontend image**
- [ ] **Step 3: Implement SPA/static caching rules**

Recommended:
- hashed Vite assets: long immutable cache
- `index.html`: no-cache/revalidate
- service worker/manifest: controlled cache headers compatible with PWA updates

- [ ] **Step 4: Add proxy timeouts appropriate for long-lived WebSockets**
- [ ] **Step 5: Build image**

```bash
docker build -f frontend/Dockerfile -t biovolt-frontend:local .
```

- [ ] **Step 6: Commit**

```bash
git add frontend/Dockerfile deploy/nginx frontend/.dockerignore scripts/test_production_nginx.sh
git commit -m "feat: serve BioVolt production PWA through Nginx"
```

---

### Task 2: Harden backend production container entrypoint

**Files:**
- Create or Modify: `backend/Dockerfile`
- Create: `backend/docker-entrypoint.sh`
- Modify: `backend/src/biovolt_backend/config.py`
- Test: `backend/tests/test_production_config.py`

Production requirements:

```text
DATABASE_URL default inside container -> sqlite+aiosqlite:////data/biovolt.db
EXPORT_DIR -> /data/exports
HOST -> 0.0.0.0
PORT -> 8000
```

Startup:
- create `/data/exports` when writable
- initialize DB deterministically through existing application startup
- fail fast on missing required secrets/config such as device token/operator PIN hash when those capabilities are enabled

Do not run multiple Uvicorn workers against the same SQLite file in the hackathon deployment unless concurrency behavior is deliberately redesigned. Default to one worker.

- [ ] **Step 1: Write production settings tests**
- [ ] **Step 2: Implement non-root container user where practical while preserving `/data` permissions**
- [ ] **Step 3: Implement entrypoint validation without printing secret values**
- [ ] **Step 4: Build backend image**

```bash
docker build -f backend/Dockerfile -t biovolt-backend:local .
```

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/docker-entrypoint.sh backend/src/biovolt_backend/config.py backend/tests/test_production_config.py
git commit -m "feat: package BioVolt backend for persistent SQLite production"
```

---

### Task 3: Replace/extend production Docker Compose topology

**Files:**
- Modify: `docker-compose.yml` or `compose.yml` according to repository convention
- Create: `compose.dev.yml`
- Create: `.env.example`
- Modify: `.gitignore`
- Create: `docs/operations/local-deployment.md`

Production services:

```yaml
services:
  backend:
    # internal only
  nginx:
    ports:
      - "80:80"
    depends_on:
      backend:
        condition: service_healthy
volumes:
  biovolt_data:
```

Optional simulator should use a Compose profile such as:

```text
profiles: ["simulation"]
```

so normal `docker compose up -d` does not silently generate fake telemetry.

- [ ] **Step 1: Make backend reachable only on Compose network in production**
- [ ] **Step 2: Mount named volume at `/data`**
- [ ] **Step 3: Add `.env.example` with placeholders only**
- [ ] **Step 4: Preserve developer direct ports in explicit `compose.dev.yml`, not production file**
- [ ] **Step 5: Document commands**

```bash
docker compose up -d
docker compose -f docker-compose.yml -f compose.dev.yml up -d
```

- [ ] **Step 6: Run Compose config validation**

```bash
docker compose config
```

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml compose.dev.yml .env.example .gitignore docs/operations/local-deployment.md
git commit -m "feat: define BioVolt offline-first production Compose stack"
```

---

### Task 4: Add container healthchecks and restart policy

**Files:**
- Modify: production Compose file
- Modify: `deploy/nginx/conf.d/operator.conf`
- Create: `scripts/check_stack_health.sh`

Backend health:

```text
GET /api/health -> 200
```

Nginx health may use a lightweight local static/health route that also verifies proxying where appropriate.

Recommended restart policy:

```text
unless-stopped
```

Do not create restart loops that hide configuration errors; entrypoint errors must remain observable via logs.

- [ ] **Step 1: Add backend healthcheck using available container HTTP tooling**
- [ ] **Step 2: Add Nginx healthcheck**
- [ ] **Step 3: Add dependency ordering based on health, not fixed sleep**
- [ ] **Step 4: Implement `scripts/check_stack_health.sh`**
- [ ] **Step 5: Kill/restart backend container and confirm recovery through Nginx**
- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml deploy/nginx/conf.d/operator.conf scripts/check_stack_health.sh
git commit -m "feat: add BioVolt production healthchecks and restart policy"
```

---

### Task 5: Verify same-origin REST and WebSocket routing

**Files:**
- Create: `backend/tests/integration/test_proxy_assumptions.py` if backend assumptions need coverage
- Create: `scripts/verify_production_routes.py`

Verification matrix:

```text
GET  /                         -> PWA
GET  /api/health               -> backend
GET  /api/system/status        -> backend
WS   /ws/dashboard             -> backend
WS   /ws/device with auth      -> backend
GET  /experiments/...          -> SPA index fallback
```

- [ ] **Step 1: Implement route verifier using standard HTTP/WebSocket client available in project tooling**
- [ ] **Step 2: Start production stack from clean containers**
- [ ] **Step 3: Verify browser routes do not produce Nginx 404**
- [ ] **Step 4: Verify device WebSocket auth semantics unchanged through proxy**
- [ ] **Step 5: Verify dashboard WebSocket stays open and receives a test update**
- [ ] **Step 6: Commit**

```bash
git add scripts/verify_production_routes.py backend/tests/integration/test_proxy_assumptions.py
git commit -m "test: verify BioVolt same-origin production routing"
```

---

### Task 6: Verify persistent SQLite and exports across recreation

**Files:**
- Create: `scripts/verify_data_persistence.sh`
- Modify: `docs/operations/local-deployment.md`

Procedure:

```text
start stack
create/persist known test record or verify existing experiment count
record database/experiment identity
docker compose down
docker compose up -d
verify record still exists
create analytics CSV export
verify export path survives backend container recreation
```

Do not run `docker compose down -v` in persistence acceptance because that explicitly destroys named volumes.

- [ ] **Step 1: Implement persistence verification script**
- [ ] **Step 2: Document volume-removal danger clearly**
- [ ] **Step 3: Run on local deployment during implementation**
- [ ] **Step 4: Commit**

```bash
git add scripts/verify_data_persistence.sh docs/operations/local-deployment.md
git commit -m "test: verify BioVolt production data persistence"
```

## Module 8.1 Exit Criteria

- [ ] Production frontend is static Nginx-served output, not Vite dev server.
- [ ] REST and WebSockets use one local origin.
- [ ] Backend has no required public host port in production.
- [ ] SQLite/exports live under persistent `/data` volume.
- [ ] Simulator is opt-in rather than normal production default.
- [ ] Healthchecks/restarts are operational and observable.
- [ ] SPA routes and WebSocket upgrade paths are verified.
- [ ] Container recreation does not delete experiment data.
