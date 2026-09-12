import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from biovolt_backend.contracts.loader import validate_payload


def test_canonical_device_example_validates():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    validate_payload("device-telemetry.v1.schema.json", payload)


def test_device_payload_without_sequence_is_rejected():
    payload = {
        "schema_version": 1,
        "device_id": "biovolt-01",
    }
    with pytest.raises(ValidationError):
        validate_payload("device-telemetry.v1.schema.json", payload)


def test_processed_payload_with_invalid_timestamp_is_rejected():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads(
        (repo / "shared/examples/processed-telemetry.example.json").read_text(encoding="utf-8")
    )
    payload["timestamp"] = "not-a-date-time"

    with pytest.raises(ValidationError):
        validate_payload("processed-telemetry.v1.schema.json", payload)
