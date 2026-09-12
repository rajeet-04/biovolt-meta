# Phase 2.7: Frontend Integration, Compose, CI, and Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the Phase 2 PWA works end to end with the Phase 1 backend and replaceable simulator, add reproducible local preview integration, enforce frontend quality gates in CI, and define offline/installability acceptance before Phase 3 begins.

**Architecture:** The frontend is built into a Node-based Vite preview image for Phase 2 integration only. Vite uses same-origin `/api` and `/ws` browser paths and a configurable proxy target: local preview defaults to `http://localhost:8000`, while Compose sets the target to `http://backend:8000`. The simulator remains optional. Production Nginx/Cloudflared deployment is still deferred.

**Tech Stack:** Node.js, Vite preview, Docker Compose, Vitest, React Testing Library, TypeScript, ESLint, GitHub Actions.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Existing Phase 0/1 tests must stay green.
- Frontend can start with backend while simulator is stopped.
- Frontend must behave identically when telemetry is later provided by real ESP32 hardware.
- No production Nginx/Cloudflared configuration enters Phase 2.
- No real secrets are committed.
- CI tests deterministic functionality; offline-installability and service-worker behavior also receive a manual browser acceptance step.
- Same-origin `/api` and `/ws` paths remain the browser-facing frontend contract.
- Proxy target configuration is deployment plumbing only and must not leak into React components.

---

### Task 1: Add configurable preview proxy and frontend Docker image

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/.dockerignore`
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/README.md`

**Interfaces:**
- Container exposes port `4173`.
- Container builds frontend then starts Vite preview on `0.0.0.0:4173`.
- Environment variable `BIOVOLT_PROXY_TARGET` controls both REST and WebSocket proxy target.
- Default proxy target: `http://localhost:8000`.

- [ ] **Step 1: Refactor Vite proxy target into one configuration value**

Use `loadEnv` in `vite.config.ts`:

```ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.BIOVOLT_PROXY_TARGET || 'http://localhost:8000'

  const proxy = {
    '/api': { target: proxyTarget, changeOrigin: true },
    '/ws': { target: proxyTarget, ws: true, changeOrigin: true },
  }

  return {
    plugins: [react()],
    server: { proxy },
    preview: { proxy },
  }
})
```

When integrating this into the actual Phase 2 Vite config, preserve the previously configured PWA plugin and test settings rather than replacing them.

- [ ] **Step 2: Add proxy-configuration test**

Test helper/config behavior for:

```text
no env -> http://localhost:8000
BIOVOLT_PROXY_TARGET=http://backend:8000 -> container target
```

Both `/api` and `/ws` must use the same target; `/ws` must set `ws: true`.

- [ ] **Step 3: Create simple integration Docker image**

Use one Node image intentionally because this is a Phase 2 preview/integration image, not the final production image:

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
ENV BIOVOLT_PROXY_TARGET=http://backend:8000
EXPOSE 4173
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
```

Production image optimization is deferred to the Nginx deployment phase.

- [ ] **Step 4: Build image**

```bash
docker build -f frontend/Dockerfile -t biovolt-frontend:phase2 .
```

Expected: successful production build and preview-capable image.

- [ ] **Step 5: Verify local preview still targets localhost**

Outside Docker:

```bash
cd frontend
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
```

With FastAPI on localhost:8000, `/api/health` through the preview origin must succeed.

- [ ] **Step 6: Commit**

```bash
git add frontend/Dockerfile frontend/.dockerignore frontend/package.json frontend/package-lock.json frontend/README.md frontend/vite.config.ts frontend/tests
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
  environment:
    BIOVOLT_PROXY_TARGET: http://backend:8000
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

The canonical test frame includes required `sequence` and may include `cumulative_energy_mj: null` in one test case.

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

### Task 5: Add Phase 2 smoke checklist document

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
sequence appears in Live Data
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

1. confirm installability/installed standalone launch on the laptop browser
2. disable external internet
3. keep local stack available and verify local telemetry still works
4. then stop backend and refresh installed/cached PWA
5. verify app shell opens
6. verify cached telemetry is explicitly labeled cached/offline
7. verify no cached data is labeled live

- [ ] **Step 5: Document source-neutral hardware handoff expectation**

Later hardware acceptance repeats the same UI checks using real `biovolt-01` telemetry with no frontend code change caused merely by replacing the simulator.

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
installability check
offline shell check
cached-data labeling check
```

- [ ] **Step 6: Keep protocol semantics unchanged**

If a frontend test exposes a contract problem, fix it through an explicit reviewed protocol/backend change. Do not silently alter Phase 0/1 field meaning solely for frontend convenience.

## Phase 2 Final Verification Command Set

```bash
python scripts/validate_schemas.py
pytest tests/contracts -v

# Run the exact Phase 1 documented backend/simulator tests.

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
- [ ] Local preview works with default localhost backend proxy target.
- [ ] Compose frontend works with `BIOVOLT_PROXY_TARGET=http://backend:8000`.
- [ ] Backend + frontend run with simulator stopped.
- [ ] Adding simulator causes live telemetry to appear without frontend restart.
- [ ] Stopping simulator does not stop frontend/backend.
- [ ] Frontend runtime integration tests pass with required `sequence` and nullable telemetry fields.
- [ ] Source replacement test proves no simulator-specific UI branch.
- [ ] Frontend GitHub Actions workflow is green.
- [ ] Phase 0 and Phase 1 regression suites remain green.
- [ ] PWA is installable with valid 192/512 icon assets.
- [ ] Installed/cached app shell opens without external internet.
- [ ] Local backend telemetry continues with external internet disabled.
- [ ] Backend-off refresh shows cached data only as cached/offline.
- [ ] No experiment controls, actuator commands, Nginx, or Cloudflared production logic has entered Phase 2.
- [ ] Phase 2 PR records verification evidence before merge.
