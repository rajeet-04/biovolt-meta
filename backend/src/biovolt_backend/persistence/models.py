"""SQLAlchemy persistence models for telemetry samples."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from biovolt_backend.persistence.database import Base


class UTCDateTime(TypeDecorator[datetime]):
    """Store aware datetimes in SQLite while restoring UTC awareness on read."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class TelemetrySample(Base):
    """A queryable processed telemetry sample with raw-payload provenance."""

    __tablename__ = "telemetry_samples"
    __table_args__ = (
        Index(
            "ix_telemetry_samples_device_cell_received",
            "device_id",
            "cell_id",
            "received_at",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    cell_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence: Mapped[int] = mapped_column(nullable=False)
    uptime_ms: Mapped[int] = mapped_column(nullable=False)

    bpv_voltage_mv: Mapped[float | None] = mapped_column(nullable=True)
    current_ua: Mapped[float | None] = mapped_column(nullable=True)
    power_uw: Mapped[float | None] = mapped_column(nullable=True)
    cumulative_energy_mj: Mapped[float | None] = mapped_column(nullable=True)
    od680: Mapped[float | None] = mapped_column(nullable=True)
    temperature_c: Mapped[float | None] = mapped_column(nullable=True)
    lux: Mapped[float | None] = mapped_column(nullable=True)
    grow_led_pwm: Mapped[int] = mapped_column(nullable=False)
    mixer_on: Mapped[bool] = mapped_column(nullable=False)
    control_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    experiment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSON(none_as_null=True), nullable=False
    )

    bpv_adc_raw: Mapped[int | None] = mapped_column(nullable=True)
    bpw34_raw: Mapped[int | None] = mapped_column(nullable=True)
    bpw34_voltage_mv: Mapped[float | None] = mapped_column(nullable=True)
