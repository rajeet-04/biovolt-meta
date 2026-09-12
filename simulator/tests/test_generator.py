from importlib import resources
from pathlib import Path

import pytest

import biovolt_simulator.generator as generator_module
from biovolt_simulator.generator import TelemetryGenerator, validate_telemetry_frame


def test_packaged_schema_matches_canonical_source() -> None:
    canonical = (
        Path(__file__).resolve().parents[2]
        / "shared"
        / "schemas"
        / "device-telemetry.v1.schema.json"
    )
    packaged = resources.files("biovolt_simulator").joinpath(
        "schemas/device-telemetry.v1.schema.json"
    )

    assert packaged.read_bytes() == canonical.read_bytes()


def test_packaged_schema_validates_without_source_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generator_module._telemetry_validator.cache_clear()
    monkeypatch.setattr(
        generator_module,
        "_repository_root",
        lambda: (_ for _ in ()).throw(RuntimeError("source tree unavailable")),
    )

    try:
        frame = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1").next_frame(
            0.0
        )
        validate_telemetry_frame(frame)
    finally:
        generator_module._telemetry_validator.cache_clear()


def test_same_seed_produces_same_first_frames() -> None:
    a = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")
    b = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")

    assert a.next_frame(0.0) == b.next_frame(0.0)
    assert a.next_frame(0.5) == b.next_frame(0.5)


def test_sequence_and_uptime_follow_elapsed_time() -> None:
    generator = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")

    first = generator.next_frame(0.0)
    second = generator.next_frame(0.5)

    assert first["sequence"] == 1
    assert second["sequence"] == 2
    assert first["uptime_ms"] == 0
    assert second["uptime_ms"] == 500


def test_elapsed_time_regression_is_rejected_without_mutating_state() -> None:
    generator = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")

    generator.next_frame(1.0)
    state_before = generator.state

    with pytest.raises(ValueError, match="must not regress"):
        generator.next_frame(0.5)

    assert generator.state == state_before
    assert generator.next_frame(1.5)["sequence"] == state_before.sequence + 1


def test_sub_millisecond_elapsed_regression_is_rejected_without_mutation() -> None:
    generator = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")

    generator.next_frame(1.0004)
    state_before = generator.state
    random_state_before = generator._random.getstate()

    with pytest.raises(ValueError, match="must not regress"):
        generator.next_frame(1.0003)

    assert generator.state == state_before
    assert generator._random.getstate() == random_state_before


def test_growth_reduces_transmitted_light_without_noise() -> None:
    generator = TelemetryGenerator(
        seed=42,
        device_id="d1",
        cell_id="c1",
        bpw34_noise_amplitude=0,
        growth_rate_per_second=0.02,
    )

    early = generator.next_frame(0.0)
    later = generator.next_frame(10.0)

    assert later["optical"]["bpw34_raw"] < early["optical"]["bpw34_raw"]


def test_generated_frame_matches_phase_zero_schema() -> None:
    generator = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1")

    validate_telemetry_frame(generator.next_frame(0.0))
    validate_telemetry_frame(generator.next_frame(0.5))


def test_raw_frame_does_not_include_derived_measurements() -> None:
    frame = TelemetryGenerator(seed=42, device_id="d1", cell_id="c1").next_frame(0)

    assert set(frame) == {
        "schema_version",
        "device_id",
        "sequence",
        "uptime_ms",
        "cell_id",
        "electrical",
        "optical",
        "environment",
        "actuators",
        "control",
        "health",
    }
    assert "current_ua" not in frame["electrical"]
    assert "power_uw" not in frame["electrical"]
    assert "od680" not in frame["optical"]
