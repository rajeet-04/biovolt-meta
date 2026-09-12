"""Pure processing of one raw BioVolt telemetry frame."""

from dataclasses import dataclass
from datetime import datetime

from biovolt_backend.contracts.models import (
    ActuatorStateProcessed,
    BiologicalProcessed,
    ControlStateProcessed,
    DeviceTelemetryV1,
    ElectricalProcessed,
    EnvironmentProcessed,
    ProcessedTelemetryV1,
)
from biovolt_backend.domain.electrical import current_ua, power_uw
from biovolt_backend.domain.optical import calculate_od680


@dataclass(frozen=True)
class ProcessingConfig:
    """Calibration and electrical settings needed for one processing pass."""

    load_resistance_ohm: float
    bpw34_dark_raw: int | None
    bpw34_blank_raw: int | None


def build_processed_telemetry(
    raw: DeviceTelemetryV1,
    timestamp: datetime,
    config: ProcessingConfig,
    cumulative_energy_mj: float,
) -> ProcessedTelemetryV1:
    """Build a schema-valid processed frame from one raw frame.

    Timestamp and cumulative energy are supplied by the caller because they are
    server-side concerns; this function does not retain state.
    """
    voltage_mv = raw.electrical.bpv_voltage_mv
    current = current_ua(voltage_mv, config.load_resistance_ohm) if voltage_mv is not None else None
    power = power_uw(voltage_mv, config.load_resistance_ohm) if voltage_mv is not None else None
    od680 = (
        calculate_od680(
            raw.optical.bpw34_raw,
            config.bpw34_dark_raw,
            config.bpw34_blank_raw,
        )
        if raw.optical.led_680_enabled and raw.health.bpw34_ok
        else None
    )

    return ProcessedTelemetryV1(
        schema_version=1,
        device_id=raw.device_id,
        cell_id=raw.cell_id,
        sequence=raw.sequence,
        timestamp=timestamp,
        electrical=ElectricalProcessed(
            voltage_mv=voltage_mv,
            current_ua=current,
            power_uw=power,
            load_resistance_ohm=config.load_resistance_ohm,
            cumulative_energy_mj=cumulative_energy_mj,
        ),
        biological=BiologicalProcessed(
            od680=od680,
            biomass_g_l=None,
            biomass_total_g=None,
            biomass_delta_g=None,
            co2_biofixed_g=None,
        ),
        environment=EnvironmentProcessed(
            temperature_c=raw.environment.temperature_c,
            lux=raw.environment.lux,
        ),
        actuators=ActuatorStateProcessed(
            grow_led_pwm=raw.actuators.grow_led_pwm,
            mixer_on=raw.actuators.mixer_on,
        ),
        control=ControlStateProcessed(mode=raw.control.mode),
    )
