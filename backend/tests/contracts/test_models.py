import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.contracts.models import DeviceTelemetryV1, ProcessedTelemetryV1


def test_raw_model_parses_canonical_example():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    model = DeviceTelemetryV1.model_validate(payload)
    assert model.schema_version == 1
    assert model.device_id
    assert model.cell_id


def test_processed_model_roundtrip_validates_against_schema():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/processed-telemetry.example.json").read_text())
    model = ProcessedTelemetryV1.model_validate(payload)

    validate_payload("processed-telemetry.v1.schema.json", model.model_dump(mode="json"))


def test_raw_model_uses_schema_adc_field_and_requires_optimizer_direction():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    model = DeviceTelemetryV1.model_validate(payload)

    assert model.electrical.bpv_adc_raw == payload["electrical"]["bpv_adc_raw"]
    assert model.control.optimizer_direction == payload["control"]["optimizer_direction"]
    assert "adc_raw" not in model.model_dump(mode="json")["electrical"]


def test_raw_model_rejects_missing_optimizer_direction():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    del payload["control"]["optimizer_direction"]

    with pytest.raises(ValidationError):
        DeviceTelemetryV1.model_validate(payload)


def test_raw_model_rejects_legacy_adc_key():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    payload["electrical"]["adc_raw"] = payload["electrical"].pop("bpv_adc_raw")

    with pytest.raises(ValidationError):
        DeviceTelemetryV1.model_validate(payload)


def test_raw_model_rejects_non_integer_adc():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    payload["electrical"]["bpv_adc_raw"] = "18431"

    with pytest.raises(ValidationError):
        DeviceTelemetryV1.model_validate(payload)


def test_raw_model_rejects_out_of_range_adc():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    payload["electrical"]["bpv_adc_raw"] = 32768

    with pytest.raises(ValidationError):
        DeviceTelemetryV1.model_validate(payload)


def test_raw_model_rejects_nested_extra_field():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    payload["electrical"]["unexpected"] = 1

    with pytest.raises(ValidationError):
        DeviceTelemetryV1.model_validate(payload)


def test_raw_model_rejects_numeric_string_sequence():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/device-telemetry.example.json").read_text())
    payload["sequence"] = "1245"

    with pytest.raises(ValidationError):
        DeviceTelemetryV1.model_validate(payload)


def test_processed_model_rejects_naive_timestamp():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/processed-telemetry.example.json").read_text())
    payload["timestamp"] = "2026-08-23T17:30:15.124"

    with pytest.raises(ValidationError):
        ProcessedTelemetryV1.model_validate(payload)


def test_processed_model_rejects_numeric_timestamp():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/processed-telemetry.example.json").read_text())
    payload["timestamp"] = 1787506215

    with pytest.raises(ValidationError):
        ProcessedTelemetryV1.model_validate(payload)


def test_processed_model_accepts_aware_datetime_and_serializes_to_schema():
    repo = Path(__file__).resolve().parents[3]
    payload = json.loads((repo / "shared/examples/processed-telemetry.example.json").read_text())
    payload["timestamp"] = datetime(2026, 8, 23, 17, 30, 15, 124000, tzinfo=UTC)

    model = ProcessedTelemetryV1.model_validate(payload)
    serialized = model.model_dump(mode="json")

    assert serialized["timestamp"] == "2026-08-23T17:30:15.124000Z"
    validate_payload("processed-telemetry.v1.schema.json", serialized)
