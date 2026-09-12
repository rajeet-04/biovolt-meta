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
    errors = sorted(
        validator.iter_errors(example), key=lambda error: list(error.absolute_path)
    )
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
