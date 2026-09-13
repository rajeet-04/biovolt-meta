"""Asynchronous experiment orchestration from device command outcomes."""

from biovolt_backend.commands.dispatcher import CommandDispatcher
from biovolt_backend.commands.schemas import CommandCreate, CommandView, DeviceAck
from biovolt_backend.commands.service import CommandService

from .schemas import ExperimentView
from .service import ExperimentService
from .state import ExperimentState


class ExperimentOrchestrator:
    """Start and stop experiments without waiting for device acknowledgements."""

    def __init__(
        self,
        experiments: ExperimentService,
        commands: CommandService,
        dispatcher: CommandDispatcher | None = None,
    ) -> None:
        self._experiments = experiments
        self._commands = commands
        self._dispatcher = dispatcher
        self._start_requirements: dict[str, set[str]] = {}
        self._stop_requirements: dict[str, set[str]] = {}

    async def start(self, experiment_id: str) -> ExperimentView:
        experiment = await self._experiments.begin_start(experiment_id)
        required: set[str] = set()
        try:
            for arm in experiment.arms:
                required.add(
                    str(
                        (
                            await self._commands.create(
                                CommandCreate(
                                    device_id=arm.device_id,
                                    experiment_id=experiment.id,
                                    kind="set_mode",
                                    payload={"mode": arm.mode},
                                )
                            )
                        ).command_id
                    )
                )
                required.add(
                    str(
                        (
                            await self._commands.create(
                                CommandCreate(
                                    device_id=arm.device_id,
                                    experiment_id=experiment.id,
                                    kind="set_led_pwm",
                                    payload={"pwm": arm.initial_led_pwm},
                                )
                            )
                        ).command_id
                    )
                )
                if arm.initial_mixer_on:
                    required.add(
                        str(
                            (
                                await self._commands.create(
                                    CommandCreate(
                                        device_id=arm.device_id,
                                        experiment_id=experiment.id,
                                        kind="set_mixer",
                                        payload={"on": True},
                                    )
                                )
                            ).command_id
                        )
                    )
        except Exception:
            await self._experiments.abort(experiment.id, "failed to create start commands")
            raise
        self._start_requirements[experiment.id] = required
        await self._dispatch_devices(experiment)
        return experiment

    async def stop(self, experiment_id: str) -> ExperimentView:
        experiment = await self._experiments.begin_stop(experiment_id)
        required: set[str] = set()
        try:
            for arm in experiment.arms:
                command = await self._commands.create(
                    CommandCreate(
                        device_id=arm.device_id,
                        experiment_id=experiment.id,
                        kind="safe_stop",
                    )
                )
                required.add(str(command.command_id))
        except Exception:
            await self._experiments.abort(experiment.id, "failed to create stop commands")
            raise
        self._stop_requirements[experiment.id] = required
        await self._dispatch_devices(experiment)
        return experiment

    async def _dispatch_devices(self, experiment: ExperimentView) -> None:
        if self._dispatcher is None:
            return
        for device_id in {arm.device_id for arm in experiment.arms}:
            await self._dispatcher.dispatch_pending_for_device(device_id)

    async def on_ack(self, command: CommandView, ack: DeviceAck) -> None:
        """Apply only terminal command outcomes to the owning experiment."""

        experiment_id = command.experiment_id
        if experiment_id is None:
            return
        experiment = await self._experiments.get(experiment_id)
        if ack.status in {"rejected", "failed"} or command.status == "expired":
            if experiment.state in {ExperimentState.STARTING, ExperimentState.STOPPING}:
                await self._experiments.abort(
                    experiment_id, ack.reason_code or "device command failed"
                )
            return
        if ack.status != "applied":
            return
        if experiment.state == ExperimentState.STARTING:
            required = self._start_requirements.get(experiment_id, set())
            if required and await self._all_applied(required):
                await self._experiments.mark_running(experiment_id)
        elif experiment.state == ExperimentState.STOPPING:
            required = self._stop_requirements.get(experiment_id, set())
            if required and await self._all_applied(required):
                await self._experiments.mark_completed(experiment_id)

    async def _all_applied(self, command_ids: set[str]) -> bool:
        statuses = [await self._commands.get(command_id) for command_id in command_ids]
        return all(command.status == "applied" for command in statuses)
