"""SQLAlchemy models for persisted experiments and arms."""

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from biovolt_backend.persistence.database import Base
from biovolt_backend.persistence.models import UTCDateTime


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    notes: Mapped[str | None] = mapped_column(String(4000))
    calibration_profile_id: Mapped[str | None] = mapped_column(String(64))
    arms: Mapped[list["ExperimentArm"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentArm(Base):
    __tablename__ = "experiment_arms"
    __table_args__ = (UniqueConstraint("experiment_id", "device_id", "cell_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    cell_id: Mapped[str] = mapped_column(String(64), nullable=False)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    initial_led_pwm: Mapped[int] = mapped_column(Integer, nullable=False)
    initial_mixer_on: Mapped[bool] = mapped_column(Boolean, nullable=False)
    label: Mapped[str | None] = mapped_column(String(128))
    experiment: Mapped[Experiment] = relationship(back_populates="arms")
