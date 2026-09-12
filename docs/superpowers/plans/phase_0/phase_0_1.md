# Phase 0.1: Repository Structure and Conventions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the BioVolt monorepo layout, ownership boundaries, repository conventions, and documentation entry points without adding runtime application code.

**Architecture:** The repository is organized by independently deployable responsibility: ESP32 firmware, backend, frontend, simulator, shared contracts, infrastructure, documentation, tests, and scripts. Directories are represented by focused README files so Git tracks the structure without meaningless empty placeholders.

**Tech Stack:** Markdown, EditorConfig, Git, Python 3.11+ only for repository-layout tests.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Do not scaffold FastAPI, React, PlatformIO, Docker, Nginx, or Cloudflared in this module.
- Do not add package managers or lockfiles.
- Keep each top-level component README focused on responsibility and Phase 1+ ownership.
- JSON and API protocol naming is `snake_case`.
- Python code later uses `snake_case`; TypeScript internal variables may use `camelCase`; C++ internal variables may use `camelCase` while serialized fields remain `snake_case`.
- Source files use UTF-8, LF line endings, and final newlines.

---

### Task 1: Add a repository-layout test first

**Files:**
- Create: `tests/contracts/test_repository_layout.py`

**Interfaces:**
- Consumes: repository root.
- Produces: `test_required_repository_entry_points_exist()` and `test_runtime_scaffolding_is_not_present_in_phase_zero()`.

- [ ] **Step 1: Write the failing repository-layout tests**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    ".editorconfig",
    "backend/README.md",
    "firmware/esp32/README.md",
    "frontend/README.md",
    "simulator/README.md",
    "docs/architecture/software-architecture.md",
    "docs/protocols/data-contract.md",
    "docs/protocols/versioning.md",
]

FORBIDDEN_PHASE_ZERO_FILES = [
    "docker-compose.yml",
    "backend/app/main.py",
    "frontend/package.json",
    "firmware/esp32/platformio.ini",
]


def test_required_repository_entry_points_exist() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    assert missing == []


def test_runtime_scaffolding_is_not_present_in_phase_zero() -> None:
    present = [path for path in FORBIDDEN_PHASE_ZERO_FILES if (ROOT / path).exists()]
    assert present == []
```

- [ ] **Step 2: Run the tests and confirm the first test fails**

Run:

```bash
python -m pytest tests/contracts/test_repository_layout.py -v
```

Expected: `test_required_repository_entry_points_exist` fails because the repository entry-point files do not exist yet. The runtime-scaffolding test should pass.

---

### Task 2: Create the root repository conventions

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `.editorconfig`

**Interfaces:**
- Consumes: architecture spec.
- Produces: human-readable repository entry point and consistent text-file behavior.

- [ ] **Step 1: Create the root README with exact Phase 0 boundaries**

The README must contain these sections:

```markdown
# BioVolt

BioVolt is an adaptive living biophotovoltaic research prototype for MetaMorph 2.0.

## Architecture
- ESP32: sensing, local safety, actuation, Perturb & Observe control
- FastAPI: scientific derivations, experiments, persistence, WebSockets
- React PWA: visualization and operator interaction

## Repository Areas
- `firmware/esp32/`
- `backend/`
- `frontend/`
- `simulator/`
- `shared/`
- `docs/`
- `scripts/`
- `tests/`

## Current Development Phase
Phase 0: repository foundation and versioned protocol contracts.

## Scientific Ownership Rule
Raw ESP32 telemetry contains measured/control-state values only. Current, power, OD680, biomass, estimated CO2 biofixed into biomass, cumulative energy, and server timestamps are derived by the backend.
```

- [ ] **Step 2: Create `.editorconfig`**

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

- [ ] **Step 3: Create `.gitignore`**

Use the following Phase 0-safe ignores:

```gitignore
# OS / editors
.DS_Store
Thumbs.db
.idea/
.vscode/

# Python
__pycache__/
*.py[cod]
.pytest_cache/
.venv/
venv/

# Environment secrets
.env
.env.*
!.env.example

# Future frontend
node_modules/
dist/

# Future PlatformIO
.pio/

# Runtime data
data/*.db
data/*.sqlite
data/*.sqlite3
data/exports/

# Coverage
.coverage
htmlcov/
```

- [ ] **Step 4: Do not add `.env.example` yet**

Phase 0 has no runtime configuration. `.env.example` belongs to the first phase that introduces actual runtime services.

---

### Task 3: Create component boundary READMEs

**Files:**
- Create: `backend/README.md`
- Create: `firmware/esp32/README.md`
- Create: `frontend/README.md`
- Create: `simulator/README.md`

**Interfaces:**
- Consumes: `docs/architecture/software-architecture.md`.
- Produces: explicit component ownership boundaries for later phases.

- [ ] **Step 1: Create `backend/README.md`**

It must state:

```markdown
# Backend

Planned owner: FastAPI service.

Responsibilities beginning in Phase 1:
- device WebSocket gateway
- dashboard WebSocket gateway
- server timestamps
- scientific derived metrics
- experiment lifecycle
- calibration profiles
- SQLite persistence
- CSV export

Phase 0 contains no backend runtime code.
```

- [ ] **Step 2: Create `firmware/esp32/README.md`**

```markdown
# ESP32 Firmware

Planned owner: ESP32 DevKit V1 using PlatformIO, Arduino Framework, and FreeRTOS.

Responsibilities beginning in the firmware phase:
- raw sensor acquisition
- actuator state
- sensor health
- local safety
- Perturb & Observe control
- sequence and uptime counters
- WebSocket device transport

Scientific derived values remain backend-owned.

Phase 0 contains no firmware runtime code.
```

- [ ] **Step 3: Create `frontend/README.md`**

```markdown
# Frontend

Planned owner: React + TypeScript installable PWA.

Responsibilities beginning in the frontend phase:
- visualization
- live charts
- experiment UI
- calibration wizard UI
- operator controls
- offline display caching

The frontend does not independently calculate backend-owned scientific metrics.

Phase 0 contains no frontend runtime code.
```

- [ ] **Step 4: Create `simulator/README.md`**

```markdown
# Device Simulator

Beginning in Phase 1, this component will emulate ESP32 device telemetry using the exact shared device-telemetry contract.

It exists so backend and frontend development can proceed without physical hardware.

Phase 0 contains no simulator runtime code.
```

---

### Task 4: Document data ownership, units, and versioning

**Files:**
- Create: `docs/protocols/data-contract.md`
- Create: `docs/protocols/versioning.md`

**Interfaces:**
- Consumes: approved software architecture.
- Produces: canonical units, ownership rules, missing-data semantics, and schema-version policy used by every later contract.

- [ ] **Step 1: Create `data-contract.md` with the canonical unit table**

The file must contain:

```markdown
# BioVolt Data Contract

## Canonical Units

| Quantity | Field suffix | Unit |
|---|---|---|
| BPV voltage | `_mv` | millivolts |
| current | `_ua` | microamperes |
| power | `_uw` | microwatts |
| cumulative energy | `_mj` | millijoules |
| resistance | `_ohm` | ohms |
| temperature | `_c` | degrees Celsius |
| light | `lux` | lux |
| biomass concentration | `_g_l` | grams/litre |
| biomass mass | `_g` | grams |
| CO2 biofixed | `_g` | grams |
| device uptime | `_ms` | milliseconds |
| server timestamp | `timestamp` | ISO 8601 with timezone |

## Ownership

ESP32 owns raw measurements, actuator state, control state, sensor health, sequence, and uptime.
FastAPI owns server timestamps and scientific derived metrics.
React owns visualization only.

## Missing Measurements
A failed or unavailable physical sensor field is `null` and its corresponding health flag is `false`. Never substitute `0` for missing data.

## Raw vs Derived
Raw telemetry must not contain `current_ua`, `power_uw`, `od680`, biomass, CO2 biofixation, or cumulative energy.
```

- [ ] **Step 2: Create `versioning.md`**

It must define:

```markdown
# Protocol Versioning

Every protocol document contains `schema_version` as an integer.
Phase 0 defines version `1`.

Compatible additions may extend a v1 schema only when old valid v1 payloads remain valid.
Breaking changes create a new schema file such as `device-telemetry.v2.schema.json`.
Existing v1 files are never silently repurposed with incompatible meanings.
```

---

### Task 5: Run and commit Module 0.1

**Files:**
- Test: `tests/contracts/test_repository_layout.py`

**Interfaces:**
- Produces: a repository layout on which every subsequent Phase 0 module depends.

- [ ] **Step 1: Run the repository-layout tests**

```bash
python -m pytest tests/contracts/test_repository_layout.py -v
```

Expected: both tests pass.

- [ ] **Step 2: Inspect the repository for forbidden runtime scaffolding**

```bash
test ! -e docker-compose.yml
test ! -e backend/app/main.py
test ! -e frontend/package.json
test ! -e firmware/esp32/platformio.ini
```

Expected: all commands return status 0.

- [ ] **Step 3: Commit repository foundation**

```bash
git add README.md .gitignore .editorconfig backend/README.md firmware/esp32/README.md frontend/README.md simulator/README.md tests/contracts/test_repository_layout.py
git commit -m "chore: initialize BioVolt repository structure"
```

- [ ] **Step 4: Commit protocol conventions**

```bash
git add docs/protocols/data-contract.md docs/protocols/versioning.md
git commit -m "docs: define BioVolt data ownership and units"
```

## Module 0.1 Exit Criteria

- [ ] Required repository entry points exist.
- [ ] Runtime implementation files remain absent.
- [ ] Component ownership is documented.
- [ ] Canonical units are documented.
- [ ] Null handling is documented.
- [ ] Raw-vs-derived ownership is documented.
- [ ] Versioning policy is documented.
- [ ] Repository-layout tests pass.
