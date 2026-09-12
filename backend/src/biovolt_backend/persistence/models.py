"""SQLAlchemy persistence models for telemetry samples."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from biovolt_backend.persistence.database import Base


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
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
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
    grow_led_pwm: Mapped[int | None] = mapped_column(nullable=True)
    mixer_on: Mapped[bool | None] = mapped_column(nullable=True)
    control_mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    experiment_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    bpv_adc_raw: Mapped[int | None] = mapped_column(nullable=True)
    bpw34_raw: Mapped[int | None] = mapped_column(nullable=True)
    bpw34_voltage_mv: Mapped[float | None] = mapped_column(nullable=True)
