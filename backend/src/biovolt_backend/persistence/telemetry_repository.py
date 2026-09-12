"""Persistence queries for processed telemetry samples."""

from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from biovolt_backend.contracts.models import DeviceTelemetryV1, ProcessedTelemetryV1
from biovolt_backend.persistence.models import TelemetrySample


class TelemetryRepository:
    """Save and query telemetry through a caller-provided session factory."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def health_check(self) -> bool:
        """Verify that the repository can reach its configured database."""

        async with self._session_factory() as session:
            await session.execute(select(1))
        return True

    async def save(
        self,
        raw: DeviceTelemetryV1,
        processed: ProcessedTelemetryV1,
        raw_payload: Mapping[str, Any],
    ) -> TelemetrySample:
        """Persist one processed frame together with its original raw payload."""

        sample = TelemetrySample(
            received_at=processed.timestamp,
            device_id=raw.device_id,
            cell_id=raw.cell_id,
            sequence=raw.sequence,
            uptime_ms=raw.uptime_ms,
            load_resistance_ohm=processed.electrical.load_resistance_ohm,
            bpv_voltage_mv=processed.electrical.voltage_mv,
            current_ua=processed.electrical.current_ua,
            power_uw=processed.electrical.power_uw,
            cumulative_energy_mj=processed.electrical.cumulative_energy_mj,
            od680=processed.biological.od680,
            temperature_c=processed.environment.temperature_c,
            lux=processed.environment.lux,
            grow_led_pwm=processed.actuators.grow_led_pwm,
            mixer_on=processed.actuators.mixer_on,
            control_mode=processed.control.mode,
            raw_payload_json=dict(raw_payload),
            bpv_adc_raw=raw.electrical.bpv_adc_raw,
            bpw34_raw=raw.optical.bpw34_raw,
            bpw34_voltage_mv=raw.optical.bpw34_voltage_mv,
        )
        async with self._session_factory() as session:
            session.add(sample)
            await session.commit()
            await session.refresh(sample)
        return sample

    async def latest(self, device_id: str, cell_id: str) -> TelemetrySample | None:
        """Return the newest sample for one device/cell pair, if present."""

        statement = (
            select(TelemetrySample)
            .where(
                TelemetrySample.device_id == device_id,
                TelemetrySample.cell_id == cell_id,
            )
            .order_by(TelemetrySample.received_at.desc(), TelemetrySample.id.desc())
            .limit(1)
        )
        async with self._session_factory() as session:
            return await session.scalar(statement)

    async def history(self, device_id: str, cell_id: str, limit: int) -> list[TelemetrySample]:
        """Return the newest bounded window in chronological order."""

        if limit <= 0:
            return []

        statement = (
            select(TelemetrySample)
            .where(
                TelemetrySample.device_id == device_id,
                TelemetrySample.cell_id == cell_id,
            )
            .order_by(TelemetrySample.received_at.desc(), TelemetrySample.id.desc())
            .limit(limit)
        )
        async with self._session_factory() as session:
            result = await session.scalars(statement)
            samples = list(result)
        samples.reverse()
        return samples
