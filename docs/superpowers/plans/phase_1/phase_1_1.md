# Phase 1.1: Backend Foundation and Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a minimal, testable FastAPI backend package with typed settings, application factory, health endpoint, and deterministic test configuration.

**Architecture:** The backend is a `src/`-layout Python package. Configuration is centralized in a Pydantic settings object. The FastAPI application is built by `create_app(settings)` so tests can inject isolated settings without mutating globals.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, Pydantic Settings, pytest, pytest-asyncio, httpx, ruff.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Phase 0 contracts must remain untouched.
- Backend package name is `biovolt_backend`.
- App construction must be dependency-injectable for tests.
- Secrets come from environment variables only.
- Default database URL points to a local SQLite file under `data/`.
- No telemetry processing, WebSocket, or persistence implementation belongs in this module.

---

### Task 1: Bootstrap backend package and tool configuration

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/src/biovolt_backend/__init__.py`
- Create: `backend/src/biovolt_backend/main.py`
- Create: `backend/tests/__init__.py`
- Modify: `backend/README.md`

**Interfaces:**
- Produces package import `biovolt_backend`.
- Produces `create_app(settings: Settings | None = None) -> FastAPI` in a later task.

- [ ] **Step 1: Add a package-import test**

Create `backend/tests/test_package.py`:

```python
def test_backend_package_imports():
    import biovolt_backend
    assert biovolt_backend is not None
```

- [ ] **Step 2: Run the test and verify failure**

Run from `backend/`:

```bash
python -m pytest tests/test_package.py -v
```

Expected: FAIL because package metadata/source layout is not configured yet.

- [ ] **Step 3: Create `backend/pyproject.toml`**

Use this dependency shape:

```toml
[project]
name = "biovolt-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.116,<1",
  "uvicorn[standard]>=0.35,<1",
  "pydantic>=2.11,<3",
  "pydantic-settings>=2.10,<3",
  "sqlalchemy>=2.0,<3",
  "aiosqlite>=0.21,<1",
  "jsonschema>=4.25,<5",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.4,<9",
  "pytest-asyncio>=1.1,<2",
  "httpx>=0.28,<1",
  "ruff>=0.12,<1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/biovolt_backend"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

Create empty `backend/src/biovolt_backend/__init__.py`.

- [ ] **Step 4: Install and re-run package test**

```bash
python -m pip install -e '.[dev]'
python -m pytest tests/test_package.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "chore: bootstrap FastAPI backend package"
```

---

### Task 2: Add typed backend settings

**Files:**
- Create: `backend/src/biovolt_backend/config.py`
- Create: `backend/tests/test_config.py`
- Create: `.env.example`

**Interfaces:**
- Produces `Settings` with:
  - `app_name: str`
  - `environment: str`
  - `database_url: str`
  - `device_shared_token: str`
  - `load_resistance_ohm: float`
  - optional OD references `bpw34_dark_raw: float | None`, `bpw34_blank_raw: float | None`

- [ ] **Step 1: Write failing settings test**

```python
from biovolt_backend.config import Settings


def test_settings_accept_test_overrides():
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        device_shared_token="test-token",
        load_resistance_ohm=100_000.0,
    )
    assert settings.environment == "test"
    assert settings.load_resistance_ohm == 100_000.0
```

- [ ] **Step 2: Run test and verify failure**

```bash
pytest tests/test_config.py -v
```

Expected: FAIL because `Settings` does not exist.

- [ ] **Step 3: Implement settings**

`config.py`:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BIOVOLT_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "BioVolt Backend"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///../data/biovolt.db"
    device_shared_token: str = Field(default="change-me", min_length=8)
    load_resistance_ohm: float = Field(default=100_000.0, gt=0)
    bpw34_dark_raw: float | None = None
    bpw34_blank_raw: float | None = None
```

- [ ] **Step 4: Add `.env.example`**

```dotenv
BIOVOLT_ENVIRONMENT=development
BIOVOLT_DATABASE_URL=sqlite+aiosqlite:///../data/biovolt.db
BIOVOLT_DEVICE_SHARED_TOKEN=replace-with-a-long-random-token
BIOVOLT_LOAD_RESISTANCE_OHM=100000
# BIOVOLT_BPW34_DARK_RAW=320
# BIOVOLT_BPW34_BLANK_RAW=23840
```

- [ ] **Step 5: Run config tests**

```bash
pytest tests/test_config.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/src/biovolt_backend/config.py backend/tests/test_config.py .env.example
git commit -m "feat: add backend runtime settings"
```

---

### Task 3: Add FastAPI application factory and health endpoint

**Files:**
- Modify: `backend/src/biovolt_backend/main.py`
- Create: `backend/src/biovolt_backend/api/__init__.py`
- Create: `backend/src/biovolt_backend/api/health.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Produces `create_app(settings: Settings | None = None) -> FastAPI`.
- Produces `GET /api/health` response:

```json
{
  "status": "ok",
  "service": "BioVolt Backend",
  "environment": "test"
}
```

- [ ] **Step 1: Write failing health test**

```python
import pytest
from httpx import ASGITransport, AsyncClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint():
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            device_shared_token="test-token-123",
        )
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 2: Run and verify failure**

```bash
pytest tests/test_health.py -v
```

Expected: FAIL because `create_app` and route do not exist.

- [ ] **Step 3: Implement route**

`api/health.py`:

```python
from fastapi import APIRouter, Request

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }
```

`main.py`:

```python
from fastapi import FastAPI

from biovolt_backend.api.health import router as health_router
from biovolt_backend.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    app = FastAPI(title=resolved.app_name)
    app.state.settings = resolved
    app.include_router(health_router)
    return app


app = create_app()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_health.py -v
```

Expected: PASS.

- [ ] **Step 5: Run local server smoke test**

```bash
uvicorn biovolt_backend.main:app --reload --app-dir src
```

Then in another terminal:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected JSON status `ok`.

- [ ] **Step 6: Commit**

```bash
git add backend/src/biovolt_backend/main.py backend/src/biovolt_backend/api backend/tests/test_health.py
git commit -m "feat: add FastAPI app factory and health endpoint"
```

---

### Task 4: Add backend quality gate commands

**Files:**
- Modify: `backend/README.md`

**Interfaces:**
- Produces documented development commands.

- [ ] **Step 1: Run current test suite**

```bash
pytest -v
```

Expected: all Phase 1.1 tests pass.

- [ ] **Step 2: Run lint and format check**

```bash
ruff check .
ruff format --check .
```

Expected: PASS.

- [ ] **Step 3: Document exact setup/run/test commands**

Add to `backend/README.md`:

```markdown
## Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e '.[dev]'
pytest -v
ruff check .
ruff format --check .
uvicorn biovolt_backend.main:app --reload --app-dir src
```
```

- [ ] **Step 4: Commit**

```bash
git add backend/README.md
git commit -m "docs: document backend development workflow"
```

## Module 1.1 Exit Criteria

- [ ] Backend package installs editable on Python 3.11+.
- [ ] Settings can be overridden in tests and loaded from environment in development.
- [ ] `.env.example` contains no real secret.
- [ ] `GET /api/health` responds successfully.
- [ ] `pytest -v`, `ruff check .`, and `ruff format --check .` pass from `backend/`.
- [ ] No telemetry, WebSocket, or database behavior has leaked into this module.
