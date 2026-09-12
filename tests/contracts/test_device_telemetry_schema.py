import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "shared/schemas/device-telemetry.v1.schema.json"
EXAMPLE_PATH = ROOT / "shared/examples/device-telemetry.example.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(load_json(SCHEMA_PATH))


def valid_payload() -> dict:
    return load_json(EXAMPLE_PATH)


def test_canonical_device_telemetry_example_is_valid() -> None:
    errors = list(validator().iter_errors(valid_payload()))
    assert errors == []


@pytest.mark.parametrize(
    "field",
    [
        "current_ua",
        "power_uw",
        "od680",
        "biomass_g_l",
        "co2_biofixed_g",
        "cumulative_energy_mj",
        "timestamp",
    ],
)
def test_raw_payload_rejects_backend_owned_derived_fields(field: str) -> None:
    payload = valid_payload()
    payload[field] = 1
    errors = list(validator().iter_errors(payload))
    assert errors


def test_temperature_may_be_null_when_health_is_false() -> None:
    payload = valid_payload()
    payload["environment"]["temperature_c"] = None
    payload["health"]["temperature_ok"] = False
    assert list(validator().iter_errors(payload)) == []


def test_lux_may_be_null_when_health_is_false() -> None:
    payload = valid_payload()
    payload["environment"]["lux"] = None
    payload["health"]["light_sensor_ok"] = False
    assert list(validator().iter_errors(payload)) == []


@pytest.mark.parametrize("pwm", [-1, 256])
def test_grow_led_pwm_outside_byte_range_is_rejected(pwm: int) -> None:
    payload = valid_payload()
    payload["actuators"]["grow_led_pwm"] = pwm
    assert list(validator().iter_errors(payload))


def test_negative_sequence_is_rejected() -> None:
    payload = valid_payload()
    payload["sequence"] = -1
    assert list(validator().iter_errors(payload))


def test_negative_uptime_is_rejected() -> None:
    payload = valid_payload()
    payload["uptime_ms"] = -1
    assert list(validator().iter_errors(payload))


def test_unknown_top_level_field_is_rejected() -> None:
    payload = valid_payload()
    payload["mystery"] = 123
    assert list(validator().iter_errors(payload))
