"""Orchestrate validation, processing, persistence, and telemetry fanout."""

import math
from collections.abc import Mapping
from datetime import UTC, datetime

from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.contracts.models import DeviceTelemetryV1, ProcessedTelemetryV1
from biovolt_backend.domain.continuity import TelemetryContinuityTracker
from biovolt_backend.domain.electrical import current_ua, power_uw
from biovolt_backend.domain.energy import EnergyAccumulator
from biovolt_backend.domain.processing import ProcessingConfig, build_processed_telemetry
from biovolt_backend.persistence.telemetry_repository import TelemetryRepository
from biovolt_backend.persistence.throttle import PersistenceThrottle
from biovolt_backend.websocket.dashboard_hub import DashboardHub
from biovolt_backend.websocket.device_registry import DeviceRegistry

STORAGE_SAFE_INT_MAX = 2**63 - 1


class TelemetryRejected(ValueError):
    """Raised when an incoming telemetry frame cannot be accepted."""


def _ensure_finite_payload(value: object) -> None:
    """Reject non-finite numbers accepted by Python's permissive JSON decoder."""

    if isinstance(value, float) and not math.isfinite(value):
        raise TelemetryRejected("non-finite telemetry value")
    if isinstance(value, Mapping):
        for nested in value.values():
            _ensure_finite_payload(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _ensure_finite_payload(nested)


def _safe_power_uw(voltage_mv: float, resistance_ohm: float) -> float:
    """Calculate power without allowing arithmetic overflow into stateful work."""

    try:
        power = power_uw(voltage_mv, resistance_ohm)
    except OverflowError as exc:
        raise TelemetryRejected("telemetry calculation overflow") from exc
    if not math.isfinite(power):
        raise TelemetryRejected("telemetry calculation overflow")
    return power


def _safe_electrical_values(voltage_mv: float, resistance_ohm: float) -> tuple[float, float]:
    """Validate both electrical derivatives before energy state is updated."""

    try:
        current = current_ua(voltage_mv, resistance_ohm)
    except OverflowError as exc:
        raise TelemetryRejected("non-finite derived electrical value") from exc
    if not math.isfinite(current):
        raise TelemetryRejected("non-finite derived electrical value")
    return current, _safe_power_uw(voltage_mv, resistance_ohm)


def _ensure_storage_safe_integers(raw: DeviceTelemetryV1) -> None:
    """Keep integer telemetry fields within the persistence model's int64 range."""

    if raw.sequence > STORAGE_SAFE_INT_MAX or raw.uptime_ms > STORAGE_SAFE_INT_MAX:
        raise TelemetryRejected("storage-unsafe telemetry integer")


class TelemetryService:
    """Process one authenticated device telemetry frame."""

    def __init__(
        self,
        config: ProcessingConfig,
        energy: EnergyAccumulator,
        throttle: PersistenceThrottle,
        repository: TelemetryRepository,
        dashboard_hub: DashboardHub,
        device_registry: DeviceRegistry,
        continuity: TelemetryContinuityTracker | None = None,
    ) -> None:
        self._config = config
        self._energy = energy
        self._continuity = continuity or TelemetryContinuityTracker()
        self._throttle = throttle
        self._repository = repository
        self._dashboard_hub = dashboard_hub
        self._device_registry = device_registry

    async def handle_raw(
        self,
        payload: dict[str, object],
        authenticated_device_id: str,
        received_at: datetime,
    ) -> ProcessedTelemetryV1:
        """Validate, process, optionally persist, and broadcast one raw frame."""

        _ensure_finite_payload(payload)
        try:
            validate_payload("device-telemetry.v1.schema.json", payload)
            raw = DeviceTelemetryV1.model_validate(payload)
        except (JsonSchemaValidationError, PydanticValidationError) as exc:
            raise TelemetryRejected("invalid telemetry payload") from exc

        if raw.device_id != authenticated_device_id:
            raise TelemetryRejected("device id mismatch")

        if received_at.tzinfo is None or received_at.utcoffset() is None:
            raise TelemetryRejected("received_at must be timezone-aware")
        received_at = received_at.astimezone(UTC)
        _ensure_storage_safe_integers(raw)

        voltage_mv = raw.electrical.bpv_voltage_mv
        _, measured_power_uw = (
            _safe_electrical_values(voltage_mv, self._config.load_resistance_ohm)
            if voltage_mv is not None
            else (None, None)
        )
        continuity = self._continuity.observe(
            raw.device_id, raw.cell_id, raw.sequence, raw.uptime_ms, commit=False
        )
        try:
            if continuity.restarted:
                self._energy.reset(raw.device_id, raw.cell_id)
                energy_mj = self._energy.anchor(
                    raw.device_id, raw.cell_id, raw.uptime_ms, measured_power_uw
                )
            elif continuity.contiguous:
                energy_mj = self._energy.update(
                    raw.device_id, raw.cell_id, raw.uptime_ms, measured_power_uw
                )
            else:
                energy_mj = self._energy.anchor(
                    raw.device_id, raw.cell_id, raw.uptime_ms, measured_power_uw
                )
        except OverflowError as exc:
            raise TelemetryRejected("cumulative energy overflow") from exc
        if not math.isfinite(energy_mj):
            raise TelemetryRejected("cumulative energy overflow")
        self._continuity.observe(raw.device_id, raw.cell_id, raw.sequence, raw.uptime_ms)
        processed = build_processed_telemetry(
            raw,
            timestamp=received_at,
            config=self._config,
            cumulative_energy_mj=energy_mj,
        )
        self._device_registry.mark_telemetry(raw.device_id, received_at)

        if self._throttle.should_persist(raw.device_id, raw.cell_id, received_at):
            await self._repository.save(raw, processed, payload)

        await self._dashboard_hub.broadcast_json(processed.model_dump(mode="json"))
        return processed
