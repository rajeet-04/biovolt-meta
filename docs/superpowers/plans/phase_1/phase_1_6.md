# Phase 1.6: Integration, Docker Compose, CI, and Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the Phase 1 backend and simulator work end to end, package them in a reproducible Docker Compose development stack, enforce tests in GitHub Actions, and define a manual 30-minute soak acceptance test before Phase 2 begins.

**Architecture:** Docker Compose runs the backend by default and enables the simulator through a `simulator` profile. GitHub Actions runs contract validation, backend tests, simulator tests, Ruff checks, and Docker configuration/build checks. End-to-end tests verify the real runtime path `simulator frame -> /ws/device -> validation -> derived metrics -> SQLite -> /ws/dashboard`.

**Tech Stack:** Docker, Docker Compose, FastAPI/Uvicorn, Python 3.11+, pytest, websockets, GitHub Actions.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Phase 0 contract tests must remain green.
- Docker Compose is development/integration orchestration in Phase 1, not final Nginx/Cloudflared production deployment.
- Backend data must persist through a named volume.
- Secrets are provided through environment variables and `.env`; real tokens are never committed.
- Simulator is optional via Compose profile so later real ESP32 testing can run backend without a conflicting fake device.
- CI uses short deterministic integration tests, not a 30-minute workflow run.
- The 30-minute soak is a manual/local Phase 1 acceptance gate.

---

### Task 1: Add backend Docker image

**Files:**
- Create: `backend/Dockerfile`
- Create: `backend/.dockerignore`
- Modify: `backend/README.md`

**Interfaces:**
- Container exposes TCP port `8000`.
- Container starts `uvicorn biovolt_backend.main:app --host 0.0.0.0 --port 8000`.

- [ ] **Step 1: Create minimal Python image definition**

Recommended shape:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY backend/pyproject.toml /app/backend/pyproject.toml
COPY backend/src /app/backend/src
RUN pip install --no-cache-dir /app/backend

WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "biovolt_backend.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
```

When implementing, verify the build context and copy paths match the root Compose context.

- [ ] **Step 2: Add `.dockerignore`**

Exclude `.venv`, `__pycache__`, `.pytest_cache`, test databases, and local `.env`.

- [ ] **Step 3: Build image**

```bash
docker build -f backend/Dockerfile -t biovolt-backend:phase1 .
```

Expected: successful build.

- [ ] **Step 4: Run standalone health smoke test**

```bash
docker run --rm -p 8000:8000 \
  -e BIOVOLT_DEVICE_SHARED_TOKEN=test-token-123 \
  -e BIOVOLT_DATABASE_URL=sqlite+aiosqlite:////tmp/biovolt.db \
  biovolt-backend:phase1
```

Then:

```bash
curl http://localhost:8000/api/health
```

Expected `status=ok`.

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/.dockerignore backend/README.md
git commit -m "chore: containerize BioVolt backend"
```

---

### Task 2: Add simulator Docker image

**Files:**
- Create: `simulator/Dockerfile`
- Create: `simulator/.dockerignore`
- Modify: `simulator/README.md`

**Interfaces:**
- Container runs `biovolt-simulator` command.
- Runtime configuration comes entirely from `BIOVOLT_SIM_*` environment variables.

- [ ] **Step 1: Create simulator image**

Use Python 3.11 slim and install the simulator package from `simulator/`.

- [ ] **Step 2: Build image**

```bash
docker build -f simulator/Dockerfile -t biovolt-simulator:phase1 .
```

Expected: successful build.

- [ ] **Step 3: Verify startup does not print token**

Run with a deliberately recognizable token and inspect logs. The literal token must not appear.

- [ ] **Step 4: Commit**

```bash
git add simulator/Dockerfile simulator/.dockerignore simulator/README.md
git commit -m "chore: containerize BioVolt simulator"
```

---

### Task 3: Add root Docker Compose development stack

**Files:**
- Create: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `README.md`

**Interfaces:**
- Service `backend`
- Service `simulator` under Compose profile `simulator`
- Named volume `biovolt-data`

Recommended Compose shape:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    ports:
      - "8000:8000"
    environment:
      BIOVOLT_ENVIRONMENT: development
      BIOVOLT_DATABASE_URL: sqlite+aiosqlite:////data/biovolt.db
      BIOVOLT_DEVICE_SHARED_TOKEN: ${BIOVOLT_DEVICE_SHARED_TOKEN}
      BIOVOLT_LOAD_RESISTANCE_OHM: ${BIOVOLT_LOAD_RESISTANCE_OHM:-100000}
      BIOVOLT_BPW34_DARK_RAW: ${BIOVOLT_BPW34_DARK_RAW:-}
      BIOVOLT_BPW34_BLANK_RAW: ${BIOVOLT_BPW34_BLANK_RAW:-}
    volumes:
      - biovolt-data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"]
      interval: 5s
      timeout: 3s
      retries: 10

  simulator:
    profiles: ["simulator"]
    build:
      context: .
      dockerfile: simulator/Dockerfile
    depends_on:
      backend:
        condition: service_healthy
    environment:
      BIOVOLT_SIM_BACKEND_WS_URL: ws://backend:8000/ws/device
      BIOVOLT_SIM_DEVICE_ID: biovolt-sim-01
      BIOVOLT_SIM_CELL_ID: cell-a
      BIOVOLT_SIM_DEVICE_TOKEN: ${BIOVOLT_DEVICE_SHARED_TOKEN}
      BIOVOLT_SIM_INTERVAL_SECONDS: 0.5
      BIOVOLT_SIM_SEED: 42

volumes:
  biovolt-data:
```

If Pydantic Settings cannot parse empty optional float environment values, omit those environment keys unless defined rather than passing empty strings.

- [ ] **Step 1: Validate Compose syntax**

```bash
docker compose config
```

Expected: valid rendered configuration with no secret value committed.

- [ ] **Step 2: Start backend only**

```bash
docker compose up --build -d backend
curl http://localhost:8000/api/health
```

Expected: healthy.

- [ ] **Step 3: Start simulator profile**

```bash
docker compose --profile simulator up --build -d
```

Then:

```bash
curl http://localhost:8000/api/system/status
```

Expected connected device includes `biovolt-sim-01`.

- [ ] **Step 4: Verify persistent volume**

Stop/restart backend without deleting volumes. Latest/history telemetry must still return previously persisted rows.

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml .env.example README.md
git commit -m "chore: add Phase 1 Docker Compose stack"
```

---

### Task 4: Add end-to-end integration test

**Files:**
- Create: `backend/tests/integration/test_device_to_dashboard.py`
- Create: `backend/tests/integration/test_persistence_cadence.py`

**Interfaces:**
- Test full ASGI path without Docker for speed and determinism.

- [ ] **Step 1: Write device-to-dashboard test**

Test sequence:
1. create test app with temporary SQLite DB and fixed token
2. connect `/ws/dashboard`
3. connect `/ws/device` with valid auth headers
4. send canonical raw payload
5. receive dashboard payload
6. assert derived current and power
7. assert server timestamp exists
8. assert raw-only fields are not incorrectly exposed as derived values

- [ ] **Step 2: Add malformed-frame isolation test**

Send malformed frame from device, then a valid frame. Assert valid frame is still accepted after malformed rejection and dashboard receives only the valid processed frame.

- [ ] **Step 3: Add persistence cadence test**

Send frames at 0, 0.5, 1.0, 1.5, 2.0 second timestamps through service/app test hooks. Expect approximately 3 persisted samples and 5 live broadcasts.

- [ ] **Step 4: Add wrong-token integration test**

Wrong token must yield policy close and zero persisted rows.

- [ ] **Step 5: Run integration suite**

```bash
cd backend
pytest tests/integration -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/tests/integration
git commit -m "test: cover Phase 1 telemetry pipeline end to end"
```

---

### Task 5: Add backend/simulator GitHub Actions workflow

**Files:**
- Create: `.github/workflows/backend.yml`

**Interfaces:**
- Runs on `push` and `pull_request`.
- Must coexist with Phase 0 `contracts.yml`.

Recommended job steps:

```yaml
name: Backend and Simulator

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -r requirements-contracts.txt
      - run: python scripts/validate_schemas.py
      - run: pytest tests/contracts -v
      - run: python -m pip install -e 'backend[dev]'
      - run: pytest backend/tests -v
      - run: ruff check backend/src backend/tests
      - run: ruff format --check backend/src backend/tests
      - run: python -m pip install -e 'simulator[dev]'
      - run: pytest simulator/tests -v
      - run: ruff check simulator/src simulator/tests
      - run: ruff format --check simulator/src simulator/tests
      - run: docker compose config
      - run: docker compose build backend simulator
```

Adjust editable-install syntax to the package manager behavior verified during implementation.

- [ ] **Step 1: Add workflow**

- [ ] **Step 2: Run the exact workflow commands locally where possible**

- [ ] **Step 3: Commit and verify GitHub Actions becomes green**

```bash
git add .github/workflows/backend.yml
git commit -m "ci: validate BioVolt backend and simulator"
```

---

### Task 6: Add Phase 1 smoke and 30-minute soak scripts

**Files:**
- Create: `scripts/phase1_smoke.py`
- Create: `scripts/soak_phase1.py`
- Modify: `README.md`

**Interfaces:**
- `phase1_smoke.py` verifies a running stack in under 30 seconds.
- `soak_phase1.py --minutes 30` performs manual acceptance monitoring.

- [ ] **Step 1: Implement smoke checks**

Smoke script should:
1. call `/api/health`
2. wait for `biovolt-sim-01` to appear in `/api/system/status`
3. call latest telemetry
4. assert `power_uw` is present when voltage is present
5. sleep 3 seconds
6. call history and assert multiple samples exist
7. exit 0 on success, nonzero on failure

- [ ] **Step 2: Implement soak checks**

Every 30 seconds during the requested duration:
- backend health must be ok
- simulator device must be connected or reconnect within a bounded grace period
- latest telemetry age must remain below 3 seconds during normal run
- history row count must continue increasing
- no invalid negative cumulative energy

At completion, calculate expected persisted row range:

```text
expected ≈ duration_seconds at 1 Hz
acceptable range = 90% to 110% of expected
```

Use bounded tolerance because startup/reconnect timing may drop a few samples.

- [ ] **Step 3: Document acceptance command**

```bash
cp .env.example .env
# set a real local shared token
docker compose --profile simulator up --build -d
python scripts/phase1_smoke.py
python scripts/soak_phase1.py --minutes 30
```

- [ ] **Step 4: Run smoke locally**

Expected: PASS.

- [ ] **Step 5: Run full 30-minute soak before Phase 1 merge**

Record start/end time and final row count in PR verification notes.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase1_smoke.py scripts/soak_phase1.py README.md
git commit -m "test: add Phase 1 smoke and soak acceptance checks"
```

## Phase 1 Final Verification Command Set

From repository root:

```bash
python scripts/validate_schemas.py
pytest tests/contracts -v

cd backend
pytest -v
ruff check src tests
ruff format --check src tests
cd ..

cd simulator
pytest -v
ruff check src tests
ruff format --check src tests
cd ..

docker compose config
docker compose build backend simulator
docker compose --profile simulator up -d
python scripts/phase1_smoke.py
python scripts/soak_phase1.py --minutes 30
```

## Module 1.6 / Phase 1 Exit Criteria

- [ ] Phase 0 contracts still pass without semantic changes.
- [ ] Backend and simulator images build successfully.
- [ ] Backend starts independently from simulator.
- [ ] Simulator profile connects with the configured token.
- [ ] Named SQLite volume survives container restart.
- [ ] End-to-end dashboard integration test proves processed telemetry fanout.
- [ ] Invalid/wrong-auth telemetry never reaches SQLite.
- [ ] 500 ms live cadence and approximately 1 Hz persistence are demonstrated.
- [ ] GitHub Actions contract/backend/simulator workflows are green.
- [ ] `phase1_smoke.py` passes.
- [ ] Manual 30-minute soak passes with telemetry freshness under normal operation and persistence row count within tolerance.
- [ ] No React, real ESP32 firmware, experiment engine, Nginx, Cloudflared, or operator-control implementation has entered Phase 1.
