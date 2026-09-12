# ruff: noqa: E501
from datetime import datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from biovolt_backend.persistence.database import Base
from biovolt_backend.persistence.models import UTCDateTime


class CalibrationProfile(Base):
    __tablename__ = "calibration_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    active_revision_id: Mapped[str | None] = mapped_column(String(36))
    revisions: Mapped[list["CalibrationRevision"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class CalibrationRevision(Base):
    __tablename__ = "calibration_revisions"
    __table_args__ = (UniqueConstraint("profile_id", "revision_number"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    profile_id: Mapped[str] = mapped_column(ForeignKey("calibration_profiles.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    source_notes: Mapped[str | None] = mapped_column(Text)
    load_resistance_ohm: Mapped[float] = mapped_column(nullable=False)
    ads1115_offset_mv: Mapped[float] = mapped_column(nullable=False)
    optical_dark_raw: Mapped[float | None] = mapped_column()
    optical_blank_raw: Mapped[float | None] = mapped_column()
    biomass_model_type: Mapped[str | None] = mapped_column(String(16))
    biomass_slope: Mapped[float | None] = mapped_column()
    biomass_intercept: Mapped[float | None] = mapped_column()
    biomass_point_count: Mapped[int | None] = mapped_column()
    biomass_r_squared: Mapped[float | None] = mapped_column()
    biomass_rmse_g_l: Mapped[float | None] = mapped_column()
    biomass_od_min: Mapped[float | None] = mapped_column()
    biomass_od_max: Mapped[float | None] = mapped_column()
    reactor_volume_l: Mapped[float | None] = mapped_column()
    co2_per_dry_biomass_g_per_g: Mapped[float | None] = mapped_column()
    temperature_offset_c: Mapped[float | None] = mapped_column()
    lux_offset: Mapped[float | None] = mapped_column()
    raw_calibration_points_json: Mapped[str | None] = mapped_column(Text)
    validation_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    profile: Mapped[CalibrationProfile] = relationship(back_populates="revisions")
