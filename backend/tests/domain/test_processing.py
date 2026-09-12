import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.contracts.models import DeviceTelemetryV1
from biovolt_backend.domain.electrical import current_ua, power_uw
from biovolt_backend.domain.optical import calculate_od680
from biovolt_backend.domain.processing import ProcessingConfig, build_processed_telemetry

REPO_ROOT = Path(__file__).resolve().parents[3]


def canonical_raw() -> DeviceTelemetryV1:
    payload = json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )
    return DeviceTelemetryV1.model_validate(payload)


def test_build_processed_telemetry_calculates_and_serializes_contract() -> None:
    raw = canonical_raw()
    timestamp = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
    config = ProcessingConfig(
        load_resistance_ohm=100_000.0,
        bpw34_dark_raw=320,
        bpw34_blank_raw=23_840,
    )

    result = build_processed_telemetry(
        raw,
        timestamp=timestamp,
        config=config,
        cumulative_energy_mj=8.431,
    )

    assert result.electrical.voltage_mv == raw.electrical.bpv_voltage_mv
    assert result.electrical.current_ua == pytest.approx(
        current_ua(raw.electrical.bpv_voltage_mv, config.load_resistance_ohm)
    )
    assert result.electrical.power_uw == pytest.approx(
        power_uw(raw.electrical.bpv_voltage_mv, config.load_resistance_ohm)
    )
    assert result.biological.od680 == pytest.approx(
        calculate_od680(
            raw.optical.bpw34_raw,
            config.bpw34_dark_raw,
            config.bpw34_blank_raw,
        )
    )
    assert result.electrical.cumulative_energy_mj == 8.431
    assert result.timestamp == timestamp

    validate_payload(
        "processed-telemetry.v1.schema.json",
        result.model_dump(mode="json"),
    )


def test_build_processed_telemetry_keeps_unavailable_derived_values_null() -> None:
    raw = canonical_raw()
    raw.electrical.bpv_voltage_mv = None
    raw.optical.bpw34_raw = 320
    config = ProcessingConfig(
        load_resistance_ohm=100_000.0,
        bpw34_dark_raw=320,
        bpw34_blank_raw=23_840,
    )

    result = build_processed_telemetry(
        raw,
        timestamp=datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
        config=config,
        cumulative_energy_mj=0.0,
    )

    assert result.electrical.voltage_mv is None
    assert result.electrical.current_ua is None
    assert result.electrical.power_uw is None
    assert result.biological.od680 is None
    assert result.biological.biomass_g_l is None
    assert result.biological.biomass_total_g is None
    assert result.biological.biomass_delta_g is None
    assert result.biological.co2_biofixed_g is None
    assert result.environment.temperature_c == raw.environment.temperature_c
    assert result.environment.lux == raw.environment.lux
    assert result.actuators.grow_led_pwm == raw.actuators.grow_led_pwm
    assert result.actuators.mixer_on == raw.actuators.mixer_on
    assert result.control.mode == raw.control.mode


def test_build_processed_telemetry_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        build_processed_telemetry(
            canonical_raw(),
            timestamp=datetime(2026, 8, 23, 12, 0),
            config=ProcessingConfig(
                load_resistance_ohm=100_000.0,
                bpw34_dark_raw=320,
                bpw34_blank_raw=23_840,
            ),
            cumulative_energy_mj=0.0,
        )
