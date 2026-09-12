# ruff: noqa: E501
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from biovolt_backend.calibration.biomass_fit import BiomassCalibrationPoint, fit_linear_biomass
from biovolt_backend.calibration.models import CalibrationProfile, CalibrationRevision
from biovolt_backend.calibration.schemas import (
    CalibrationProfileView,
    CalibrationRevisionCreate,
    CalibrationRevisionView,
)


class CalibrationService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    @staticmethod
    def _view(revision: CalibrationRevision) -> CalibrationRevisionView:
        return CalibrationRevisionView(
            id=revision.id,
            profile_id=revision.profile_id,
            revision_number=revision.revision_number,
            validation=json.loads(revision.validation_json),
            biomass_slope=revision.biomass_slope,
            biomass_intercept=revision.biomass_intercept,
            biomass_r_squared=revision.biomass_r_squared,
            biomass_rmse_g_l=revision.biomass_rmse_g_l,
            biomass_point_count=revision.biomass_point_count,
        )

    async def create_profile(self, request: CalibrationRevisionCreate) -> CalibrationRevisionView:
        async with self._session_factory() as session:
            profile = CalibrationProfile(
                name=request.name, description=request.description, created_at=datetime.now(UTC)
            )
            revision = self._build_revision(request, profile.id, 1)
            profile.revisions.append(revision)
            session.add(profile)
            await session.commit()
            return self._view(revision)

    async def revise(
        self, profile_id: str, request: CalibrationRevisionCreate
    ) -> CalibrationRevisionView:
        async with self._session_factory() as session:
            profile = await session.scalar(
                select(CalibrationProfile)
                .options(selectinload(CalibrationProfile.revisions))
                .where(CalibrationProfile.id == profile_id)
            )
            if profile is None:
                raise KeyError(profile_id)
            number = max((r.revision_number for r in profile.revisions), default=0) + 1
            revision = self._build_revision(request, profile.id, number)
            profile.revisions.append(revision)
            await session.commit()
            return self._view(revision)

    async def activate(self, revision_id: str) -> CalibrationRevisionView:
        async with self._session_factory() as session:
            revision = await session.get(CalibrationRevision, revision_id)
            if revision is None:
                raise KeyError(revision_id)
            profile = await session.get(CalibrationProfile, revision.profile_id)
            profile.active_revision_id = revision.id
            await session.commit()
            return self._view(revision)

    async def list_profiles(self) -> list[CalibrationProfileView]:
        async with self._session_factory() as session:
            profiles = list(await session.scalars(select(CalibrationProfile)))
            return [
                CalibrationProfileView(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    active_revision_id=p.active_revision_id,
                    revisions=[self._view(r) for r in p.revisions],
                )
                for p in profiles
            ]

    @staticmethod
    def _build_revision(
        request: CalibrationRevisionCreate, profile_id: str, number: int
    ) -> CalibrationRevision:
        points = [
            BiomassCalibrationPoint(p.od680, p.dry_biomass_g_l) for p in request.biomass_points
        ]
        validation: dict[str, str] = {}
        fit = None
        try:
            fit = fit_linear_biomass(points)
        except ValueError as exc:
            if points:
                validation["biomass"] = str(exc)
        return CalibrationRevision(
            profile_id=profile_id,
            revision_number=number,
            created_at=datetime.now(UTC),
            source_notes=request.source_notes,
            load_resistance_ohm=request.load_resistance_ohm,
            ads1115_offset_mv=request.ads1115_offset_mv,
            optical_dark_raw=request.optical_dark_raw,
            optical_blank_raw=request.optical_blank_raw,
            biomass_model_type="linear" if fit else None,
            biomass_slope=fit.slope_g_l_per_od if fit else None,
            biomass_intercept=fit.intercept_g_l if fit else None,
            biomass_point_count=fit.point_count if fit else None,
            biomass_r_squared=fit.r_squared if fit else None,
            biomass_rmse_g_l=fit.rmse_g_l if fit else None,
            biomass_od_min=fit.od_min if fit else None,
            biomass_od_max=fit.od_max if fit else None,
            reactor_volume_l=request.reactor_volume_l,
            co2_per_dry_biomass_g_per_g=request.co2_per_dry_biomass_g_per_g,
            raw_calibration_points_json=json.dumps(
                [p.model_dump() for p in request.biomass_points]
            ),
            validation_json=json.dumps(validation),
        )
