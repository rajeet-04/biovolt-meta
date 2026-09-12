# ruff: noqa: E501
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from biovolt_backend.calibration.models import CalibrationRevision
from biovolt_backend.calibration.types import (
    BiomassCalibration,
    OpticalCalibration,
    ReactorCalibration,
)
from biovolt_backend.domain.biomass import derive_biomass
from biovolt_backend.domain.optical_density import derive_od680
from biovolt_backend.experiments.models import Experiment, ExperimentArm
from biovolt_backend.persistence.models import TelemetrySample


class BaselineService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def capture(
        self, experiment_id: str, arm_id: str, now: datetime | None = None
    ) -> dict[str, object]:
        now = now or datetime.now(UTC)
        async with self._session_factory() as session:
            experiment = await session.scalar(
                select(Experiment)
                .options(selectinload(Experiment.arms))
                .where(Experiment.id == experiment_id)
            )
            arm = next(
                (item for item in (experiment.arms if experiment else []) if item.id == arm_id),
                None,
            )
            if experiment is None or arm is None:
                raise HTTPException(404, "experiment arm not found")
            if experiment.state != "ready":
                raise HTTPException(409, "baseline capture requires a ready experiment")
            if arm.baseline_sequence is not None:
                return self._view(arm)
            revision = (
                await session.get(CalibrationRevision, arm.calibration_revision_id)
                if arm.calibration_revision_id
                else None
            )
            if (
                revision is None
                or revision.optical_dark_raw is None
                or revision.optical_blank_raw is None
                or revision.biomass_slope is None
                or revision.biomass_intercept is None
                or revision.biomass_od_min is None
                or revision.biomass_od_max is None
                or revision.reactor_volume_l is None
            ):
                raise HTTPException(422, "arm calibration is incomplete")
            sample = await session.scalar(
                select(TelemetrySample)
                .where(
                    TelemetrySample.device_id == arm.device_id,
                    TelemetrySample.cell_id == arm.cell_id,
                )
                .order_by(TelemetrySample.received_at.desc())
                .limit(1)
            )
            if sample is None or (now - sample.received_at).total_seconds() > 3:
                raise HTTPException(409, "fresh telemetry is required")
            od = derive_od680(
                sample.bpw34_raw,
                OpticalCalibration(revision.optical_dark_raw, revision.optical_blank_raw),
            )
            biomass = derive_biomass(
                od.od680,
                BiomassCalibration(
                    "linear",
                    revision.biomass_slope,
                    revision.biomass_intercept,
                    revision.biomass_point_count or 0,
                    revision.biomass_r_squared,
                    revision.biomass_rmse_g_l,
                    revision.biomass_od_min,
                    revision.biomass_od_max,
                ),
                ReactorCalibration(
                    revision.reactor_volume_l, revision.co2_per_dry_biomass_g_per_g or 1
                ),
            )
            if not biomass.eligible or biomass.dry_biomass_g is None:
                raise HTTPException(422, "biomass baseline is unavailable")
            arm.baseline_telemetry_sample_id = sample.id
            arm.baseline_sequence = sample.sequence
            arm.baseline_timestamp = sample.received_at
            arm.baseline_biomass_g_l = biomass.biomass_g_l
            arm.baseline_dry_biomass_g = biomass.dry_biomass_g
            await session.commit()
            return self._view(arm)

    @staticmethod
    def _view(arm: ExperimentArm) -> dict[str, object]:
        return {
            "arm_id": arm.id,
            "baseline_sequence": arm.baseline_sequence,
            "baseline_timestamp": arm.baseline_timestamp,
            "baseline_biomass_g_l": arm.baseline_biomass_g_l,
            "baseline_dry_biomass_g": arm.baseline_dry_biomass_g,
        }
