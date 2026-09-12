import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def assert_valid(schema_path: str, example_path: str) -> None:
    schema = load_json(schema_path)
    example = load_json(example_path)
    errors = list(Draft202012Validator(schema).iter_errors(example))
    assert errors == []


def test_device_command_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/device-command.v1.schema.json",
        "shared/examples/device-command.example.json",
    )


def test_device_ack_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/device-ack.v1.schema.json",
        "shared/examples/device-ack.example.json",
    )


def test_calibration_profile_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/calibration-profile.v1.schema.json",
        "shared/examples/calibration-profile.example.json",
    )


def test_experiment_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/experiment.v1.schema.json",
        "shared/examples/experiment.example.json",
    )


def test_system_event_example_is_valid() -> None:
    assert_valid(
        "shared/schemas/system-event.v1.schema.json",
        "shared/examples/system-event.example.json",
    )


@pytest.mark.parametrize("invalid_pwm", [-1, 256])
def test_set_led_pwm_rejects_values_outside_byte_range(invalid_pwm: int) -> None:
    schema = load_json("shared/schemas/device-command.v1.schema.json")
    payload = load_json("shared/examples/device-command.example.json")
    payload["payload"] = {"pwm": invalid_pwm}
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_unknown_command_type_is_rejected() -> None:
    schema = load_json("shared/schemas/device-command.v1.schema.json")
    payload = load_json("shared/examples/device-command.example.json")
    payload["kind"] = "do_magic"
    payload["payload"] = {}
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_command_payloads_are_strict_and_require_fields() -> None:
    schema = load_json("shared/schemas/device-command.v1.schema.json")
    payload = load_json("shared/examples/device-command.example.json")
    payload["payload"] = {"pwm": 96, "gpio": 26}
    assert list(Draft202012Validator(schema).iter_errors(payload))
    payload["payload"] = {}
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_ack_rejects_unknown_status_reason_and_missing_command_id() -> None:
    schema = load_json("shared/schemas/device-ack.v1.schema.json")
    payload = load_json("shared/examples/device-ack.example.json")
    payload["status"] = "done"
    assert list(Draft202012Validator(schema).iter_errors(payload))
    payload = load_json("shared/examples/device-ack.example.json")
    payload["reason_code"] = "mystery"
    assert list(Draft202012Validator(schema).iter_errors(payload))
    payload = load_json("shared/examples/device-ack.example.json")
    del payload["command_id"]
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_calibration_rejects_nonpositive_load_resistance() -> None:
    schema = load_json("shared/schemas/calibration-profile.v1.schema.json")
    payload = load_json("shared/examples/calibration-profile.example.json")
    payload["electrical"]["load_resistance_ohm"] = 0
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_calibration_rejects_nonpositive_reactor_volume() -> None:
    schema = load_json("shared/schemas/calibration-profile.v1.schema.json")
    payload = load_json("shared/examples/calibration-profile.example.json")
    payload["reactor"]["volume_l"] = 0
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_unknown_experiment_mode_is_rejected() -> None:
    schema = load_json("shared/schemas/experiment.v1.schema.json")
    payload = load_json("shared/examples/experiment.example.json")
    payload["mode"] = "turbo"
    assert list(Draft202012Validator(schema).iter_errors(payload))


def test_experiment_definition_rejects_runtime_timestamp_fields() -> None:
    schema = load_json("shared/schemas/experiment.v1.schema.json")
    payload = load_json("shared/examples/experiment.example.json")
    payload["started_at"] = "2026-08-23T17:00:00+05:30"
    assert list(Draft202012Validator(schema).iter_errors(payload))
