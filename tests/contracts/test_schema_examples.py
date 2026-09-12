import json
import subprocess
import sys
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


def test_all_contract_files_exist() -> None:
    missing = []
    for schema_path, example_path in CONTRACTS.values():
        if not (ROOT / schema_path).is_file():
            missing.append(schema_path)
        if not (ROOT / example_path).is_file():
            missing.append(example_path)
    assert missing == []


def test_all_canonical_examples_are_schema_version_one() -> None:
    for _, example_path in CONTRACTS.values():
        payload = json.loads((ROOT / example_path).read_text(encoding="utf-8"))
        assert payload["schema_version"] == 1


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
