# Phase 2.7: Frontend Integration, Compose, CI, and Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the Phase 2 PWA works end to end with the Phase 1 backend and replaceable simulator, add reproducible local preview integration, enforce frontend quality gates in CI, and define offline/installability acceptance before Phase 3 begins.

**Architecture:** The frontend is built into a Node-based Vite preview image for Phase 2 integration only. Vite preview proxies `/api` and `/ws` to the existing backend service so the browser uses same-origin routes. The simulator remains optional. Production Nginx/Cloudflared deployment is still deferred.

**Tech Stack:** Node.js, Vite preview, Docker Compose, Vitest, React Testing Library, TypeScript, ESLint, GitHub Actions.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Existing Phase 0/1 tests must stay green.
- Frontend can start with backend while simulator is stopped.
- Frontend must behave identically when telemetry is later provided by real ESP32 hardware.
- No production Nginx/Cloudflared configuration enters Phase 2.
- No real secrets are committed.
- CI tests deterministic functionality; offline-installability and service-worker behavior also receive a manual browser acceptance step.
- Same-origin `/api` and `/ws` paths remain the frontend contract.

---

### Task 1: Add frontend preview Docker image

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`
- Modify: `frontend/package.json`
- Modify: `frontend/README.md`

**Interfaces:**
- Container exposes port `4173`.
- Container builds frontend then starts Vite preview on `0.0.0.0:4173`.

- [ ] **Step 1: Create deterministic Node image**

Recommended shape:

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY --from=build /app/package.json /app/package-lock.json ./
RUN npm ci --omit=dev=false
COPY --from=build /app/dist ./dist
COPY --from=build /app/vite.config.ts ./vite.config.ts
EXPOSE 4173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
```

If preview requires TypeScript config dependencies at runtime, verify image contents during implementation and simplify to the smallest working image rather than guessing.

- [ ] **Step 2: Configure Vite preview proxy**

`preview.proxy` must route:

```text
/api -> http://backend:8000
/ws  -> ws://backend:8000 with ws=true
```

Development proxy remains localhost-oriented; preview proxy is container-oriented.

- [ ] **Step 3: Build image**

```bash
docker build -f frontend/Dockerfile -t biovolt-frontend:phase2 .
```

Expected: successful production build.

- [ ] **Step 4: Commit**

```bash
git add frontend/Dockerfile frontend/.dockerignore frontend/package.json frontend/README.md frontend/vite.config.ts
git commit -m "chore: containerize BioVolt PWA preview"
```

---

### Task 2: Extend Docker Compose with optional frontend profile

**Files:**
- Modify: root `docker-compose.yml`
- Modify: root `README.md`

**Interfaces:**
- Existing `backend` remains unchanged.
- Existing `simulator` remains optional.
- New `frontend` service uses profile `frontend` and exposes `4173:4173`.

Recommended service shape:

```yaml
frontend:
  profiles: ["frontend"]
  build:
    context: .
    dockerfile: frontend/Dockerfile
  depends_on:
    backend:
      condition: service_healthy
  ports:
    - "4173:4173"
```

- [ ] **Step 1: Validate backend-only stack still renders**

```bash
docker compose config
```

Existing backend behavior must not require the frontend profile.

- [ ] **Step 2: Start backend + frontend without simulator**

```bash
docker compose --profile frontend up --build -d
```

Open `http://localhost:4173`. Expected: PWA shell loads and reports no connected device/waiting state rather than crashing.

- [ ] **Step 3: Add simulator optionally**

```bash
docker compose --profile frontend --profile simulator up --build -d
```

Expected: Overview transitions to live telemetry without frontend restart.

- [ ] **Step 4: Stop simulator only**

```bash
docker compose stop simulator
```

Expected: frontend remains running and transitions to stale/disconnected/cached state according to actual backend state.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml README.md
git commit -m "chore: add optional BioVolt PWA Compose profile"
```

---

### Task 3: Add frontend integration tests around mocked backend interfaces

**Files:**
- Create: `frontend/tests/integration/test_dashboard_runtime.tsx`
- Create: `frontend/tests/integration/test_source_replacement.tsx`

**Interfaces:**
- Test runtime can inject fake REST client and fake dashboard socket factory.

- [ ] **Step 1: Test live dashboard runtime**

Flow:

```text
mount app
socket connects
valid processed frame arrives
Overview displays exact current/power/OD680
system status reports connected source
```

- [ ] **Step 2: Test malformed dashboard message isolation**

Invalid frame is ignored/reported; next valid frame still renders.

- [ ] **Step 3: Test source replacement neutrality**

First send `device_id=biovolt-sim-01`, then clear/reset test runtime and send otherwise equivalent payload with `device_id=biovolt-01`. Assert the same component structure/metric labels are used and no `Simulator` label appears automatically.

This is a frontend contract test only. It must not import simulator code.

- [ ] **Step 4: Test backend disconnect to cached state**

After valid frame/cache write, simulate socket loss. UI must preserve last value only with non-live cached/stale indication.

- [ ] **Step 5: Run and commit**

```bash
cd frontend
npm run test:run
npm run typecheck
git add tests/integration
git commit -m "test: cover BioVolt PWA runtime integration"
```

---

### Task 4: Add frontend GitHub Actions workflow

**Files:**
- Create: `.github/workflows/frontend.yml`

**Interfaces:**
- Runs on `push` and `pull_request`.
- Coexists with Phase 0 contracts and Phase 1 backend workflows.

Recommended workflow:

```yaml
name: Frontend

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
        working-directory: frontend
      - run: npm run lint
        working-directory: frontend
      - run: npm run typecheck
        working-directory: frontend
      - run: npm run test:run
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
      - run: docker compose config
      - run: docker compose build frontend
```

- [ ] **Step 1: Add workflow**

- [ ] **Step 2: Run exact npm commands locally**

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test:run
npm run build
```

- [ ] **Step 3: Validate Compose/image build locally**

```bash
docker compose config
docker compose build frontend
```

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/frontend.yml
git commit -m "ci: validate BioVolt PWA"
```

---

### Task 5: Add Phase 2 smoke checklist script/document

**Files:**
- Create: `scripts/phase2_smoke.md`
- Modify: root `README.md`

**Interfaces:**
- This is an explicit deterministic operator checklist because browser service-worker/installability behavior is difficult to prove completely from simple shell scripts without adding a full browser automation stack.

- [ ] **Step 1: Document startup**

```bash
cp .env.example .env
# configure local device shared token
docker compose --profile frontend --profile simulator up --build -d
```

- [ ] **Step 2: Document live checks**

At `http://localhost:4173` verify:

```text
Overview loads
source appears
connection says Live
voltage/current/power appear
OD680 shows value only if backend has valid optical references
charts accumulate live data
System page shows backend/device status
```

- [ ] **Step 3: Document simulator-removal check**

```bash
docker compose stop simulator
```

Verify frontend remains up and does not crash or identify simulator-specific logic.

- [ ] **Step 4: Document offline PWA check**

After application shell has loaded and service worker is active:

1. disable external internet
2. keep local stack available and verify local telemetry still works
3. then stop backend and refresh installed/cached PWA
4. verify app shell opens
5. verify cached telemetry is explicitly labeled cached/offline
6. verify no cached data is labeled live

- [ ] **Step 5: Document source-neutral hardware handoff expectation**

Later hardware acceptance repeats the same UI checks using real `biovolt-01` telemetry with no frontend rebuild other than ordinary deployment.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase2_smoke.md README.md
git commit -m "docs: add Phase 2 PWA acceptance checklist"
```

---

### Task 6: Run final Phase 2 verification

**Files:**
- No new source file required.
- Record results in Phase 2 PR verification notes.

- [ ] **Step 1: Run Phase 0 contracts**

```bash
python scripts/validate_schemas.py
pytest tests/contracts -v
```

- [ ] **Step 2: Run Phase 1 backend/simulator test suites**

Use the exact documented Phase 1 commands. All must stay green.

- [ ] **Step 3: Run frontend quality gates**

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test:run
npm run build
cd ..
```

- [ ] **Step 4: Run Compose integration**

```bash
docker compose config
docker compose --profile frontend --profile simulator up --build -d
```

Execute `scripts/phase2_smoke.md` exactly.

- [ ] **Step 5: Record acceptance evidence**

PR notes must record:

```text
frontend build result
frontend test result
backend/contract regression result
live dashboard check
simulator-stop check
offline shell check
cached-data labeling check
```

- [ ] **Step 6: Commit any documentation-only verification adjustment if necessary**

Do not change protocol semantics merely to make frontend tests convenient.

## Phase 2 Final Verification Command Set

```bash
python scripts/validate_schemas.py
pytest tests/contracts -v

# Phase 1 documented backend/simulator tests

cd frontend
npm ci
npm run lint
npm run typecheck
npm run test:run
npm run build
cd ..

docker compose config
docker compose build frontend
docker compose --profile frontend --profile simulator up -d
```

Then execute the browser acceptance steps in `scripts/phase2_smoke.md`.

## Module 2.7 / Phase 2 Exit Criteria

- [ ] Frontend image builds.
- [ ] Backend + frontend run with simulator stopped.
- [ ] Adding simulator causes live telemetry to appear without frontend restart.
- [ ] Stopping simulator does not stop frontend/backend.
- [ ] Frontend runtime integration tests pass.
- [ ] Source replacement test proves no simulator-specific UI branch.
- [ ] Frontend GitHub Actions workflow is green.
- [ ] Phase 0 and Phase 1 regression suites remain green.
- [ ] Installed/cached app shell opens without external internet.
- [ ] Local backend telemetry continues with external internet disabled.
- [ ] Backend-off refresh shows cached data only as cached/offline.
- [ ] No experiment controls, actuator commands, Nginx, or Cloudflared production logic has entered Phase 2.
- [ ] Phase 2 PR records verification evidence before merge.
