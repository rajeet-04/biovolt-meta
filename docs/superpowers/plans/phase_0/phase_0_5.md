# Phase 0.5: Validation, CI, and Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one deterministic validation command, full schema-example coverage, GitHub Actions enforcement, and a final acceptance gate proving Phase 0 is complete before Phase 1 begins.

**Architecture:** Contract validation is intentionally lightweight. A Python script validates every canonical example against the matching versioned JSON Schema. Pytest adds negative and repository-boundary tests. GitHub Actions runs both commands on pushes and pull requests so later phases cannot silently drift the shared protocol.

**Tech Stack:** Python 3.11+, `jsonschema`, `pytest`, GitHub Actions.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- Contract tooling must have no runtime dependency on FastAPI, React, PlatformIO, Docker, or a database.
- The validation command must run from repository root.
- The validation script must return exit code 0 only when every canonical example validates.
- The validation script must print which contract failed and why.
- CI must run on `push` and `pull_request`.
- CI must use Python 3.11 or newer.
- Phase 0 is not complete until repository-layout tests, raw telemetry tests, processed telemetry tests, control-contract tests, and canonical-example validation all pass.

---

### Task 1: Add contract-tool dependencies

**Files:**
- Create: `requirements-contracts.txt`

**Interfaces:**
- Produces: minimal dependency set for local validation and CI.

- [ ] **Step 1: Create the requirements file**

```text
jsonschema>=4.23,<5
pytest>=8,<9
```

- [ ] **Step 2: Verify the dependency set is intentionally limited**

Run:

```bash
cat requirements-contracts.txt
```

Expected: exactly the two dependency lines above. Do not add application dependencies in Phase 0.

---

### Task 2: Write the validator tests before the validator

**Files:**
- Create: `tests/contracts/test_schema_examples.py`

**Interfaces:**
- Consumes: all schemas/examples from Modules 0.2 through 0.4.
- Produces: tests for complete schema/example pairing and the CLI validator behavior.

- [ ] **Step 1: Define the canonical contract mapping in the test**

```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONTRACTS = {
    "device telemetry": (
        "shared/schemas/device-telemetry.v1.schema.json",
        "shared/examples/device-telemetry.example.json",
    ),
    "processed telemetry": (
        "shared/schemas/processed-telemetry.v1.schema.json",
        "shared/examples/processed-telemetry.example.json",
    ),
    "device command": (
        "shared/schemas/device-command.v1.schema.json",
        "shared/examples/device-command.example.json",
    ),
    "calibration profile": (
        "shared/schemas/calibration-profile.v1.schema.json",
        "shared/examples/calibration-profile.example.json",
    ),
    "experiment": (
        "shared/schemas/experiment.v1.schema.json",
        "shared/examples/experiment.example.json",
    ),
    "system event": (
        "shared/schemas/system-event.v1.schema.json",
        "shared/examples/system-event.example.json",
    ),
}
```

- [ ] **Step 2: Add a test proving every declared file exists**

```python
def test_all_contract_files_exist() -> None:
    missing = []
    for schema_path, example_path in CONTRACTS.values():
        if not (ROOT / schema_path).is_file():
            missing.append(schema_path)
        if not (ROOT / example_path).is_file():
            missing.append(example_path)
    assert missing == []
```

- [ ] **Step 3: Add a test proving schema versions remain v1**

```python
import json


def test_all_canonical_examples_are_schema_version_one() -> None:
    for _, example_path in CONTRACTS.values():
        payload = json.loads((ROOT / example_path).read_text(encoding="utf-8"))
        assert payload["schema_version"] == 1
```

- [ ] **Step 4: Add a subprocess test for the future validator script**

```python
import subprocess
import sys


def test_validator_script_succeeds() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/validate_schemas.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "6/6 schemas valid" in completed.stdout
```

- [ ] **Step 5: Run the tests and confirm the validator test fails because the script does not yet exist**

```bash
python -m pytest tests/contracts/test_schema_examples.py -v
```

Expected: file-existence/version tests pass if prior modules are complete; validator subprocess test fails because `scripts/validate_schemas.py` is missing.

---

### Task 3: Implement the deterministic schema validator

**Files:**
- Create: `scripts/validate_schemas.py`

**Interfaces:**
- Consumes: six schema/example pairs.
- Produces: command-line validation with deterministic exit status used locally and by CI.

- [ ] **Step 1: Implement the validator with the same six contract pairs**

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

CONTRACTS = {
    "device telemetry": (
        "shared/schemas/device-telemetry.v1.schema.json",
        "shared/examples/device-telemetry.example.json",
    ),
    "processed telemetry": (
        "shared/schemas/processed-telemetry.v1.schema.json",
        "shared/examples/processed-telemetry.example.json",
    ),
    "device command": (
        "shared/schemas/device-command.v1.schema.json",
        "shared/examples/device-command.example.json",
    ),
    "calibration profile": (
        "shared/schemas/calibration-profile.v1.schema.json",
        "shared/examples/calibration-profile.example.json",
    ),
    "experiment": (
        "shared/schemas/experiment.v1.schema.json",
        "shared/examples/experiment.example.json",
    ),
    "system event": (
        "shared/schemas/system-event.v1.schema.json",
        "shared/examples/system-event.example.json",
    ),
}


def load_json(relative_path: str) -> dict:
    path = ROOT / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract(name: str, schema_path: str, example_path: str) -> list[str]:
    schema = load_json(schema_path)
    example = load_json(example_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(example), key=lambda error: list(error.absolute_path))
    messages = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{name}: {location}: {error.message}")
    return messages


def main() -> int:
    valid_count = 0
    all_errors: list[str] = []

    for name, (schema_path, example_path) in CONTRACTS.items():
        try:
            errors = validate_contract(name, schema_path, example_path)
        except (OSError, json.JSONDecodeError) as exc:
            errors = [f"{name}: {exc}"]

        if errors:
            print(f"FAIL {name}")
            all_errors.extend(errors)
        else:
            print(f"OK   {name}")
            valid_count += 1

    if all_errors:
        print()
        for error in all_errors:
            print(error)
        print(f"\n{valid_count}/{len(CONTRACTS)} schemas valid")
        return 1

    print(f"\n{valid_count}/{len(CONTRACTS)} schemas valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the validator directly**

```bash
python scripts/validate_schemas.py
```

Expected output contains:

```text
OK   device telemetry
OK   processed telemetry
OK   device command
OK   calibration profile
OK   experiment
OK   system event

6/6 schemas valid
```

- [ ] **Step 3: Run the validator tests again**

```bash
python -m pytest tests/contracts/test_schema_examples.py -v
```

Expected: all tests pass.

---

### Task 4: Add GitHub Actions contract enforcement

**Files:**
- Create: `.github/workflows/contracts.yml`

**Interfaces:**
- Consumes: `requirements-contracts.txt`, validator, and all contract tests.
- Produces: CI gate for every push and pull request.

- [ ] **Step 1: Create the workflow**

```yaml
name: Contract Validation

on:
  push:
  pull_request:

jobs:
  contracts:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
          cache-dependency-path: requirements-contracts.txt

      - name: Install contract dependencies
        run: python -m pip install -r requirements-contracts.txt

      - name: Validate canonical schemas
        run: python scripts/validate_schemas.py

      - name: Run contract tests
        run: python -m pytest tests/contracts -v
```

- [ ] **Step 2: Keep CI intentionally contract-only**

Do not add frontend builds, firmware builds, Docker builds, database services, or backend tests. Those do not exist in Phase 0.

---

### Task 5: Add a Phase 0 final acceptance test

**Files:**
- Modify: `tests/contracts/test_repository_layout.py`

**Interfaces:**
- Consumes: complete Phase 0 file set.
- Produces: one test that prevents merging an incomplete Phase 0 repository.

- [ ] **Step 1: Extend the required-file list with the full Phase 0 outputs**

Add:

```python
REQUIRED_FILES += [
    "requirements-contracts.txt",
    "scripts/validate_schemas.py",
    ".github/workflows/contracts.yml",
    "shared/schemas/device-telemetry.v1.schema.json",
    "shared/schemas/processed-telemetry.v1.schema.json",
    "shared/schemas/device-command.v1.schema.json",
    "shared/schemas/calibration-profile.v1.schema.json",
    "shared/schemas/experiment.v1.schema.json",
    "shared/schemas/system-event.v1.schema.json",
    "shared/examples/device-telemetry.example.json",
    "shared/examples/processed-telemetry.example.json",
    "shared/examples/device-command.example.json",
    "shared/examples/calibration-profile.example.json",
    "shared/examples/experiment.example.json",
    "shared/examples/system-event.example.json",
]
```

- [ ] **Step 2: Run the complete Phase 0 test suite**

```bash
python -m pytest tests/contracts -v
```

Expected: all tests pass.

---

### Task 6: Perform the Superpowers self-review against the spec

**Files:**
- Review only; modify Phase 0 files if a discrepancy is found.

**Interfaces:**
- Consumes: `docs/architecture/software-architecture.md` and all Phase 0 outputs.
- Produces: a verified Phase 0 boundary before commit/merge.

- [ ] **Step 1: Verify spec coverage**

Confirm all of these are represented in contracts or documentation:

```text
raw BPV voltage
BPW34 raw optical acquisition
temperature
lux
actuator state
control mode
health flags
sequence
uptime
server timestamp ownership
current derivation
power derivation
OD680 derivation
biomass calibration
estimated CO2 biofixed wording
cumulative energy field
four experiment modes
commands
calibration profile
system events
schema versioning
null handling
```

- [ ] **Step 2: Verify no runtime implementation leaked into Phase 0**

```bash
test ! -e docker-compose.yml
test ! -e backend/app/main.py
test ! -e frontend/package.json
test ! -e firmware/esp32/platformio.ini
```

Expected: all commands succeed.

- [ ] **Step 3: Scan Phase 0 plans and protocol docs for forbidden planning placeholders**

```bash
if grep -R -n -E '\bTBD\b|\bTODO\b|implement later|fill in details' docs/superpowers/plans/phase_0 docs/protocols; then
  exit 1
fi
```

Expected: no matches.

- [ ] **Step 4: Run both official verification commands**

```bash
python scripts/validate_schemas.py
python -m pytest tests/contracts -v
```

Expected: both return status 0.

---

### Task 7: Commit and push the final Phase 0 validation layer

**Files:**
- Create: `requirements-contracts.txt`
- Create: `scripts/validate_schemas.py`
- Create: `tests/contracts/test_schema_examples.py`
- Create: `.github/workflows/contracts.yml`
- Modify: `tests/contracts/test_repository_layout.py`

**Interfaces:**
- Produces: completed, CI-enforced Phase 0.

- [ ] **Step 1: Commit**

```bash
git add requirements-contracts.txt scripts/validate_schemas.py tests/contracts/test_schema_examples.py tests/contracts/test_repository_layout.py .github/workflows/contracts.yml
git commit -m "test: add contract validation and CI"
```

- [ ] **Step 2: Verify branch history contains the planned Phase 0 commit sequence**

```bash
git log --oneline --decorate -10
```

Expected to include the Phase 0 commits from the overview, with no unrelated application implementation.

- [ ] **Step 3: Push the implementation branch only after all verification passes**

For the planned implementation workflow:

```bash
git push -u origin phase/00-foundation
```

Do not push partial failing contract code as the final Phase 0 state.

## Phase 0 Final Exit Criteria

- [ ] `python scripts/validate_schemas.py` reports `6/6 schemas valid`.
- [ ] `python -m pytest tests/contracts -v` passes.
- [ ] GitHub Actions contract workflow is present.
- [ ] Canonical raw telemetry excludes backend-owned derived metrics.
- [ ] Canonical processed telemetry includes current, power, OD680, biomass, estimated CO2 biofixed, and cumulative energy.
- [ ] Commands, calibration, experiment definitions, and events are versioned.
- [ ] All component boundaries and units are documented.
- [ ] No FastAPI, React, ESP32 runtime, Docker, Nginx, or Cloudflared implementation exists yet.
- [ ] Phase 1 can consume the contracts without guessing field names or units.
