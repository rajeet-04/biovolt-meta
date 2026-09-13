from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    ".editorconfig",
    "pyproject.toml",
    "uv.lock",
    "backend/README.md",
    "firmware/esp32/README.md",
    "frontend/README.md",
    "simulator/README.md",
    "docs/architecture/software-architecture.md",
    "docs/protocols/data-contract.md",
    "docs/protocols/versioning.md",
]

REQUIRED_FILES += [
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
    # Docker Compose was introduced by Phase 1.6 and removed from this list at
    # that time. The frontend package manifest was introduced by Phase 2.1 and
    # removed from this list as part of Phase 2.7 verification. Firmware
    # PlatformIO and a top-level backend main module remain forbidden until
    # their owning phases (3.x and 1.x respectively) land.
    "backend/app/main.py",
    "firmware/esp32/platformio.ini",
]


def test_required_repository_entry_points_exist() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    assert missing == []


def test_runtime_scaffolding_is_not_present_in_phase_zero() -> None:
    present = [path for path in FORBIDDEN_PHASE_ZERO_FILES if (ROOT / path).exists()]
    assert present == []
