from collections import defaultdict

from fastapi import HTTPException

from biovolt_backend.domain.quality import DerivationQuality
from biovolt_backend.experiments.repository import ExperimentRepository

from .comparison import compare_energy
from .repository import AnalyticsRepository
from .schemas import (
    AnalyticsSeriesPoint,
    AnalyticsSeriesView,
    AnalyticsSummary,
    EnergyComparisonView,
)
from .types import AnalyticsSample
from .windows import select_matched_window


class AnalyticsService:
    def __init__(self, experiments: ExperimentRepository, repository: AnalyticsRepository) -> None:
        self._experiments, self._repository = experiments, repository

    async def summary(self, experiment_id: str) -> AnalyticsSummary:
        experiment = await self._experiments.get(experiment_id)
        if experiment is None:
            raise HTTPException(404, "experiment not found")
        return AnalyticsSummary(
            experiment_id=experiment.id,
            evidence_class=experiment.evidence_class,
            arm_count=len(experiment.arms),
        )

    async def comparison(
        self, experiment_id: str, passive_arm_id: str, adaptive_arm_id: str
    ) -> EnergyComparisonView:
        experiment = await self._experiment(experiment_id)
        passive_arm, adaptive_arm = self._arms(experiment, passive_arm_id, adaptive_arm_id)
        started = experiment.started_at or experiment.created_at
        passive = tuple(await self._samples(experiment, passive_arm, started))
        adaptive = tuple(await self._samples(experiment, adaptive_arm, started))
        result = compare_energy(
            select_matched_window(passive, adaptive, started),
            evidence_class=experiment.evidence_class,
        )
        from .quality import summarize_quality

        p_quality, a_quality = summarize_quality(passive), summarize_quality(adaptive)
        return EnergyComparisonView(
            **result.__dict__,
            passive_coverage_fraction=p_quality.power_coverage_fraction,
            adaptive_coverage_fraction=a_quality.power_coverage_fraction,
            passive_sample_count=len(passive),
            adaptive_sample_count=len(adaptive),
        )

    async def series(self, experiment_id: str, bucket_seconds: int = 10) -> AnalyticsSeriesView:
        if bucket_seconds < 1 or bucket_seconds > 300:
            raise HTTPException(422, "bucket_seconds must be between 1 and 300")
        experiment = await self._experiment(experiment_id)
        started = experiment.started_at or experiment.created_at
        grouped: dict[int, dict[str, list[float | bool]]] = defaultdict(lambda: defaultdict(list))
        for arm in experiment.arms:
            key = (
                "passive"
                if arm.mode == "passive"
                else "adaptive"
                if arm.mode == "adaptive"
                else None
            )
            if key is None:
                continue
            for sample in await self._samples(experiment, arm, started):
                bucket = int(
                    max(0, (sample.received_at - started).total_seconds()) // bucket_seconds
                )
                values = grouped[bucket]
                if sample.power_uw is not None:
                    values[f"{key}_power_uw"].append(sample.power_uw)
                values[f"{key}_led_pwm"].append(sample.grow_led_pwm)
                values[f"{key}_mixer_on"].append(sample.mixer_on)
        points = []
        for bucket in sorted(grouped):
            values = grouped[bucket]
            points.append(
                AnalyticsSeriesPoint(
                    elapsed_s=bucket * bucket_seconds,
                    passive_power_uw=self._average(values, "passive_power_uw"),
                    adaptive_power_uw=self._average(values, "adaptive_power_uw"),
                    passive_led_pwm=self._average(values, "passive_led_pwm"),
                    adaptive_led_pwm=self._average(values, "adaptive_led_pwm"),
                    passive_mixer_on=bool(values["passive_mixer_on"][-1])
                    if values.get("passive_mixer_on")
                    else None,
                    adaptive_mixer_on=bool(values["adaptive_mixer_on"][-1])
                    if values.get("adaptive_mixer_on")
                    else None,
                )
            )
        return AnalyticsSeriesView(
            experiment_id=experiment.id, bucket_seconds=bucket_seconds, points=tuple(points)
        )

    @staticmethod
    def _average(values: dict[str, list[float | bool]], name: str) -> float | None:
        entries = [value for value in values.get(name, []) if isinstance(value, (int, float))]
        return sum(entries) / len(entries) if entries else None

    async def export_rows(self, experiment_id: str) -> list[dict[str, object]]:
        experiment = await self._experiment(experiment_id)
        started = experiment.started_at or experiment.created_at
        rows: list[dict[str, object]] = []
        for arm in experiment.arms:
            for sample in await self._samples(experiment, arm, started):
                rows.append(
                    {
                        "experiment_id": experiment.id,
                        "arm_id": arm.id,
                        "arm_mode": arm.mode,
                        "device_id": arm.device_id,
                        "cell_id": arm.cell_id,
                        "received_at": sample.received_at.isoformat(),
                        "elapsed_s": (sample.received_at - started).total_seconds(),
                        "sequence": sample.sequence,
                        "uptime_ms": sample.uptime_ms,
                        "power_uw": sample.power_uw,
                        "cumulative_energy_mj": sample.cumulative_energy_mj,
                        "od680": sample.od680,
                        "grow_led_pwm": sample.grow_led_pwm,
                        "mixer_on": sample.mixer_on,
                    }
                )
        return rows

    async def _experiment(self, experiment_id: str):
        experiment = await self._experiments.get(experiment_id)
        if experiment is None:
            raise HTTPException(404, "experiment not found")
        return experiment

    @staticmethod
    def _arms(experiment, passive_arm_id: str, adaptive_arm_id: str):
        by_id = {arm.id: arm for arm in experiment.arms}
        passive, adaptive = by_id.get(passive_arm_id), by_id.get(adaptive_arm_id)
        if (
            passive is None
            or adaptive is None
            or passive.mode != "passive"
            or adaptive.mode != "adaptive"
        ):
            raise HTTPException(422, "explicit passive and adaptive arm ids are required")
        return passive, adaptive

    async def _samples(self, experiment, arm, started):
        rows = await self._repository.arm_samples(
            experiment.id,
            arm.device_id,
            arm.cell_id,
            started_at=started,
            ended_at=experiment.ended_at,
        )
        return [
            AnalyticsSample(
                received_at=row.received_at,
                sequence=row.sequence,
                uptime_ms=row.uptime_ms,
                power_uw=row.power_uw,
                cumulative_energy_mj=row.cumulative_energy_mj,
                od680=row.od680,
                biomass_g_l=None,
                dry_biomass_g=None,
                temperature_c=row.temperature_c,
                grow_led_pwm=row.grow_led_pwm,
                mixer_on=row.mixer_on,
                quality=DerivationQuality(
                    electrical_eligible=row.power_uw is not None,
                    od_eligible=row.od680 is not None,
                    biomass_eligible=False,
                    carbon_eligible=False,
                    biomass_extrapolated=False,
                    reasons=[],
                ),
            )
            for row in rows
        ]
