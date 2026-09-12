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
