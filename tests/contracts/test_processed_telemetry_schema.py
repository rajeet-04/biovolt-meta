import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "shared/schemas/processed-telemetry.v1.schema.json"
EXAMPLE_PATH = ROOT / "shared/examples/processed-telemetry.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(SCHEMA_PATH))


def payload() -> dict:
    return load_json(EXAMPLE_PATH)


def test_canonical_processed_telemetry_example_is_valid() -> None:
    assert list(validator().iter_errors(payload())) == []


def test_processed_electrical_group_contains_current_power_and_energy() -> None:
    electrical = payload()["electrical"]
    assert "current_ua" in electrical
    assert "power_uw" in electrical
    assert "cumulative_energy_mj" in electrical


def test_processed_biological_group_contains_od_biomass_and_carbon() -> None:
    biological = payload()["biological"]
    assert "od680" in biological
    assert "biomass_g_l" in biological
    assert "biomass_total_g" in biological
    assert "biomass_delta_g" in biological
    assert "co2_biofixed_g" in biological


def test_processed_payload_requires_server_timestamp() -> None:
    data = payload()
    del data["timestamp"]
    assert list(validator().iter_errors(data))


def test_negative_load_resistance_is_rejected() -> None:
    data = payload()
    data["electrical"]["load_resistance_ohm"] = -100
    assert list(validator().iter_errors(data))


def test_negative_cumulative_energy_is_rejected() -> None:
    data = payload()
    data["electrical"]["cumulative_energy_mj"] = -0.1
    assert list(validator().iter_errors(data))


@pytest.mark.parametrize(
    "group,field",
    [
        ("electrical", "current_ua"),
        ("electrical", "power_uw"),
        ("biological", "od680"),
        ("biological", "biomass_g_l"),
        ("biological", "co2_biofixed_g"),
    ],
)
def test_derived_values_may_be_null_when_inputs_are_unavailable(
    group: str, field: str
) -> None:
    data = payload()
    data[group][field] = None
    assert list(validator().iter_errors(data)) == []
