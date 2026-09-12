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

FORBIDDEN_PHASE_ZERO_FILES = [
    # Docker Compose is introduced by Phase 1.6; retain the remaining
    # runtime-entrypoint guards for Phase 0 repository completeness.
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
