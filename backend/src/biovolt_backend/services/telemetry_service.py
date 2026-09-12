"""Orchestrate validation, processing, persistence, and telemetry fanout."""

from datetime import datetime

from jsonschema.exceptions import ValidationError as JsonSchemaValidationError
from pydantic import ValidationError as PydanticValidationError

from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.contracts.models import DeviceTelemetryV1, ProcessedTelemetryV1
from biovolt_backend.domain.electrical import power_uw
from biovolt_backend.domain.energy import EnergyAccumulator
from biovolt_backend.domain.processing import ProcessingConfig, build_processed_telemetry
from biovolt_backend.persistence.telemetry_repository import TelemetryRepository
from biovolt_backend.persistence.throttle import PersistenceThrottle
from biovolt_backend.websocket.dashboard_hub import DashboardHub
from biovolt_backend.websocket.device_registry import DeviceRegistry


class TelemetryRejected(ValueError):
    """Raised when an incoming telemetry frame cannot be accepted."""


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
    ) -> None:
        self._config = config
        self._energy = energy
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

        try:
            validate_payload("device-telemetry.v1.schema.json", payload)
            raw = DeviceTelemetryV1.model_validate(payload)
        except (JsonSchemaValidationError, PydanticValidationError) as exc:
            raise TelemetryRejected("invalid telemetry payload") from exc

        if raw.device_id != authenticated_device_id:
            raise TelemetryRejected("device id mismatch")

        voltage_mv = raw.electrical.bpv_voltage_mv
        measured_power_uw = (
            power_uw(voltage_mv, self._config.load_resistance_ohm)
            if voltage_mv is not None
            else None
        )
        energy_mj = self._energy.update(
            raw.device_id,
            raw.cell_id,
            raw.uptime_ms,
            measured_power_uw,
        )
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
