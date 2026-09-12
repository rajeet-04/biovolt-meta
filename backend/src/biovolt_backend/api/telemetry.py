"""Read-only telemetry REST endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter(prefix="/api/telemetry")


def _timestamp_text(value: datetime) -> str:
    aware = (
        value
        if value.tzinfo is not None and value.utcoffset() is not None
        else value.replace(tzinfo=UTC)
    )
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _serialize_sample(sample: Any, load_resistance_ohm: float) -> dict[str, Any]:
    """Expose a persisted sample in the processed telemetry shape."""

    timestamp = _timestamp_text(sample.received_at)
    return {
        "id": sample.id,
        "schema_version": 1,
        "device_id": sample.device_id,
        "cell_id": sample.cell_id,
        "sequence": sample.sequence,
        "uptime_ms": sample.uptime_ms,
        "timestamp": timestamp,
        "received_at": timestamp,
        "electrical": {
            "voltage_mv": sample.bpv_voltage_mv,
            "current_ua": sample.current_ua,
            "power_uw": sample.power_uw,
            "load_resistance_ohm": load_resistance_ohm,
            "cumulative_energy_mj": sample.cumulative_energy_mj,
        },
        "biological": {
            "od680": sample.od680,
            "biomass_g_l": None,
            "biomass_total_g": None,
            "biomass_delta_g": None,
            "co2_biofixed_g": None,
        },
        "environment": {
            "temperature_c": sample.temperature_c,
            "lux": sample.lux,
        },
        "actuators": {
            "grow_led_pwm": sample.grow_led_pwm,
            "mixer_on": sample.mixer_on,
        },
        "control": {"mode": sample.control_mode},
    }


@router.get("/latest")
async def latest_telemetry(
    request: Request,
    device_id: str,
    cell_id: str,
) -> dict[str, Any]:
    """Return the newest persisted processed sample for one device/cell."""

    sample = await request.app.state.telemetry_repository.latest(device_id, cell_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="telemetry not found")
    return _serialize_sample(sample, request.app.state.settings.load_resistance_ohm)


@router.get("/history")
async def telemetry_history(
    request: Request,
    device_id: str,
    cell_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    """Return a bounded chronological window of processed samples."""

    samples = await request.app.state.telemetry_repository.history(device_id, cell_id, limit)
    return [
        _serialize_sample(sample, request.app.state.settings.load_resistance_ohm)
        for sample in samples
    ]
