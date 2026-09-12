import json
from pathlib import Path

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
