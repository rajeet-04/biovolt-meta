from copy import deepcopy

import pytest

from biovolt_simulator.faults import SUPPORTED_FAULTS, apply_fault
from biovolt_simulator.generator import TelemetryGenerator, validate_telemetry_frame


@pytest.fixture
def base_frame() -> dict[str, object]:
    return TelemetryGenerator(seed=42, device_id="d1", cell_id="c1").next_frame(0.0)


@pytest.mark.parametrize(
    ("fault", "section", "value_key", "health_key"),
    [
        ("temperature_null", "environment", "temperature_c", "temperature_ok"),
        ("light_null", "environment", "lux", "light_sensor_ok"),
        ("bpv_voltage_null", "electrical", "bpv_voltage_mv", "ads1115_ok"),
        ("bpw34_null", "optical", "bpw34_raw", "bpw34_ok"),
    ],
)
def test_sensor_null_fault_clears_value_and_health(
    base_frame: dict[str, object],
    fault: str,
    section: str,
    value_key: str,
    health_key: str,
) -> None:
    original = deepcopy(base_frame)

    faulted = apply_fault(base_frame, fault)

    assert faulted[section][value_key] is None  # type: ignore[index]
    assert faulted["health"][health_key] is False  # type: ignore[index]
    assert base_frame == original
    validate_telemetry_frame(faulted)


def test_faulted_generator_frames_are_schema_valid_and_do_not_mutate_state() -> None:
    generator = TelemetryGenerator(
        seed=42,
        device_id="d1",
        cell_id="c1",
        fault="temperature_null",
    )

    first = generator.next_frame(0.0)
    second = generator.next_frame(0.5)

    validate_telemetry_frame(first)
    validate_telemetry_frame(second)
    assert first["environment"]["temperature_c"] is None  # type: ignore[index]
    assert second["sequence"] == first["sequence"] + 1


def test_unknown_fault_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown simulator fault"):
        apply_fault({}, "not-a-real-fault")

    with pytest.raises(ValueError, match="unknown simulator fault"):
        TelemetryGenerator(fault="not-a-real-fault")


def test_supported_faults_are_explicit() -> None:
    assert SUPPORTED_FAULTS == frozenset(
        {"temperature_null", "light_null", "bpv_voltage_null", "bpw34_null"}
    )
