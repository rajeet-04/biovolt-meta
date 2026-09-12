"""System status endpoints."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/system")


def _timestamp_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    aware = (
        value
        if value.tzinfo is not None and value.utcoffset() is not None
        else value.replace(tzinfo=UTC)
    )
    return aware.astimezone(UTC).isoformat().replace("+00:00", "Z")


@router.get("/status")
async def system_status(request: Request) -> dict[str, Any]:
    """Return backend, database, and connected-device freshness state."""

    registry = request.app.state.device_registry
    connected_devices = registry.connected_device_ids()
    try:
        database_ok = await request.app.state.telemetry_repository.health_check()
    except Exception:
        database_ok = False
    now = datetime.now(UTC)
    devices: dict[str, dict[str, int | str | None]] = {}
    for device_id in connected_devices:
        latest = registry.latest_telemetry_at(device_id)
        age_ms = None
        if latest is not None:
            aware_latest = (
                latest
                if latest.tzinfo is not None and latest.utcoffset() is not None
                else latest.replace(tzinfo=UTC)
            )
            age_ms = max(0, int((now - aware_latest.astimezone(UTC)).total_seconds() * 1000))
        devices[device_id] = {
            "latest_telemetry_at": _timestamp_text(latest),
            "latest_telemetry_age_ms": age_ms,
        }

    return {
        "backend": "ok",
        "database": "ok" if database_ok else "error",
        "connected_devices": connected_devices,
        "device_count": len(connected_devices),
        "devices": devices,
    }
