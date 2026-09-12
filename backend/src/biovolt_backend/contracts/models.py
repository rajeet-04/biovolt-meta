from datetime import datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field


def _validate_timestamp_input(value: object) -> object:
    if isinstance(value, str):
        return value
    if isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None:
        return value
    raise ValueError("timestamp must be an ISO string or timezone-aware datetime")


ProcessedTimestamp = Annotated[AwareDatetime, BeforeValidator(_validate_timestamp_input)]


class ElectricalRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    bpv_voltage_mv: float | None
    bpv_adc_raw: int | None = Field(ge=-32768, le=32767)


class OpticalRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    bpw34_raw: int | None = Field(ge=-32768, le=32767)
    bpw34_voltage_mv: float | None
    led_680_enabled: bool


class EnvironmentRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    temperature_c: float | None = Field(ge=-55, le=125)
    lux: float | None = Field(ge=0)


class ActuatorStateRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    grow_led_pwm: int = Field(ge=0, le=255)
    mixer_on: bool


class ControlStateRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["monitor", "passive", "adaptive", "manual"]
    optimizer_direction: Literal[-1, 0, 1]


class HealthStateRaw(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    ads1115_ok: bool
    bpw34_ok: bool
    temperature_ok: bool
    light_sensor_ok: bool


class DeviceTelemetryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    device_id: str = Field(min_length=1, max_length=64)
    sequence: int = Field(ge=0)
    uptime_ms: int = Field(ge=0)
    cell_id: str = Field(min_length=1, max_length=64)
    electrical: ElectricalRaw
    optical: OpticalRaw
    environment: EnvironmentRaw
    actuators: ActuatorStateRaw
    control: ControlStateRaw
    health: HealthStateRaw


class ElectricalProcessed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    voltage_mv: float | None
    current_ua: float | None
    power_uw: float | None
    load_resistance_ohm: float = Field(gt=0)
    cumulative_energy_mj: float | None = Field(ge=0)


class BiologicalProcessed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    od680: float | None = Field(ge=0)
    biomass_g_l: float | None = Field(ge=0)
    biomass_total_g: float | None = Field(ge=0)
    biomass_delta_g: float | None
    co2_biofixed_g: float | None = Field(ge=0)


class EnvironmentProcessed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    temperature_c: float | None
    lux: float | None = Field(ge=0)


class ActuatorStateProcessed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    grow_led_pwm: int = Field(ge=0, le=255)
    mixer_on: bool


class ControlStateProcessed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    mode: Literal["monitor", "passive", "adaptive", "manual"]


class ProcessedTelemetryV1(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal[1]
    device_id: str = Field(min_length=1, max_length=64)
    cell_id: str = Field(min_length=1, max_length=64)
    sequence: int = Field(ge=0)
    timestamp: ProcessedTimestamp = Field(strict=False)
    electrical: ElectricalProcessed
    biological: BiologicalProcessed
    environment: EnvironmentProcessed
    actuators: ActuatorStateProcessed
    control: ControlStateProcessed
