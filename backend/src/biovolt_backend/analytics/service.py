from fastapi import HTTPException

from biovolt_backend.experiments.repository import ExperimentRepository

from .repository import AnalyticsRepository
from .schemas import AnalyticsSummary


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
