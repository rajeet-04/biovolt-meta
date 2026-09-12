from datetime import UTC, datetime
from uuid import uuid4

from fastapi import HTTPException

from .models import Experiment, ExperimentArm
from .repository import ExperimentRepository
from .schemas import ExperimentArmInput, ExperimentCreate, ExperimentDraftUpdate, ExperimentView
from .state import ExperimentState, can_transition


class ExperimentService:
    def __init__(self, repository: ExperimentRepository) -> None:
        self._repository = repository

    def _view(self, value: Experiment) -> ExperimentView:
        return ExperimentView.model_validate(
            {
                "id": value.id,
                "name": value.name,
                "state": value.state,
                "description": value.description,
                "notes": value.notes,
                "arms": [
                    {
                        "id": arm.id,
                        "device_id": arm.device_id,
                        "cell_id": arm.cell_id,
                        "mode": arm.mode,
                        "initial_led_pwm": arm.initial_led_pwm,
                        "initial_mixer_on": arm.initial_mixer_on,
                        "label": arm.label,
                        "calibration_revision_id": arm.calibration_revision_id,
                        "adaptive": {
                            "initial_pwm": arm.adaptive_initial_pwm,
                            "pwm_min": arm.adaptive_pwm_min,
                            "pwm_max": arm.adaptive_pwm_max,
                            "pwm_step": arm.adaptive_pwm_step,
                            "settle_ms": arm.adaptive_settle_ms,
                            "minimum_valid_samples": arm.adaptive_minimum_valid_samples,
                            "objective_deadband_fraction": arm.adaptive_deadband_fraction,
                            "mixer_policy": arm.adaptive_mixer_policy,
                            "mixer_period_ms": arm.adaptive_mixer_period_ms,
                            "mixer_on_ms": arm.adaptive_mixer_on_ms,
                        }
                        if arm.mode == "adaptive"
                        else None,
                        "baseline_sequence": arm.baseline_sequence,
                        "baseline_timestamp": arm.baseline_timestamp,
                        "baseline_biomass_g_l": arm.baseline_biomass_g_l,
                        "baseline_dry_biomass_g": arm.baseline_dry_biomass_g,
                    }
                    for arm in value.arms
                ],
            }
        )

    def _arms(self, inputs: list[ExperimentArmInput], experiment_id: str) -> list[ExperimentArm]:
        arms: list[ExperimentArm] = []
        for item in inputs:
            values = item.model_dump(exclude={"adaptive"})
            adaptive = item.adaptive
            if adaptive is not None:
                values.update(
                    adaptive_initial_pwm=adaptive.initial_pwm,
                    adaptive_pwm_min=adaptive.pwm_min,
                    adaptive_pwm_max=adaptive.pwm_max,
                    adaptive_pwm_step=adaptive.pwm_step,
                    adaptive_settle_ms=adaptive.settle_ms,
                    adaptive_minimum_valid_samples=adaptive.minimum_valid_samples,
                    adaptive_deadband_fraction=adaptive.objective_deadband_fraction,
                    adaptive_mixer_policy=adaptive.mixer_policy,
                    adaptive_mixer_period_ms=adaptive.mixer_period_ms,
                    adaptive_mixer_on_ms=adaptive.mixer_on_ms,
                )
            arms.append(ExperimentArm(id=str(uuid4()), experiment_id=experiment_id, **values))
        return arms

    async def create(self, request: ExperimentCreate) -> ExperimentView:
        now = datetime.now(UTC)
        experiment_id = str(uuid4())
        value = Experiment(
            id=experiment_id,
            name=request.name,
            state=ExperimentState.DRAFT,
            description=request.description,
            created_at=now,
            updated_at=now,
            arms=self._arms(request.arms, experiment_id),
        )
        return self._view(await self._repository.save(value))

    async def get(self, experiment_id: str) -> ExperimentView:
        value = await self._repository.get(experiment_id)
        if value is None:
            raise HTTPException(404, "experiment not found")
        return self._view(value)

    async def list(self) -> list[ExperimentView]:
        return [self._view(value) for value in await self._repository.list()]

    async def update_draft(
        self, experiment_id: str, request: ExperimentDraftUpdate
    ) -> ExperimentView:
        value = await self._repository.get(experiment_id)
        if value is None:
            raise HTTPException(404, "experiment not found")
        if value.state != ExperimentState.DRAFT:
            if (
                request.notes is not None
                and request.name is None
                and request.description is None
                and request.arms is None
            ):
                value.notes = request.notes
            else:
                raise HTTPException(409, "experiment is immutable")
        else:
            for field in ("name", "description", "notes"):
                change = getattr(request, field)
                if change is not None:
                    setattr(value, field, change)
            if request.arms is not None:
                value.arms = self._arms(request.arms, value.id)
        value.updated_at = datetime.now(UTC)
        return self._view(await self._repository.save(value))

    async def _transition(self, experiment_id: str, target: ExperimentState) -> ExperimentView:
        value = await self._repository.get(experiment_id)
        if value is None:
            raise HTTPException(404, "experiment not found")
        current = ExperimentState(value.state)
        if not can_transition(current, target):
            raise HTTPException(409, "invalid experiment transition")
        if target == ExperimentState.READY:
            if not value.arms or any(arm.mode not in {"passive", "manual"} for arm in value.arms):
                raise HTTPException(422, "ready requires passive or manual arms")
        value.state, value.updated_at = target, datetime.now(UTC)
        if target == ExperimentState.RUNNING:
            value.started_at = value.updated_at
        if target in {ExperimentState.COMPLETED, ExperimentState.ABORTED}:
            value.ended_at = value.updated_at
        return self._view(await self._repository.save(value))

    async def mark_ready(self, experiment_id: str) -> ExperimentView:
        return await self._transition(experiment_id, ExperimentState.READY)

    async def begin_start(self, experiment_id: str) -> ExperimentView:
        return await self._transition(experiment_id, ExperimentState.STARTING)

    async def mark_running(self, experiment_id: str) -> ExperimentView:
        return await self._transition(experiment_id, ExperimentState.RUNNING)

    async def begin_stop(self, experiment_id: str) -> ExperimentView:
        return await self._transition(experiment_id, ExperimentState.STOPPING)

    async def mark_completed(self, experiment_id: str) -> ExperimentView:
        return await self._transition(experiment_id, ExperimentState.COMPLETED)

    async def abort(self, experiment_id: str, reason: str | None = None) -> ExperimentView:
        value = await self._transition(experiment_id, ExperimentState.ABORTED)
        if reason:
            return await self.update_draft(experiment_id, ExperimentDraftUpdate(notes=reason))
        return value
