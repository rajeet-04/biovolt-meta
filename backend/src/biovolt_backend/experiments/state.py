"""Explicit experiment lifecycle transitions."""

from enum import StrEnum


class ExperimentState(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ABORTED = "aborted"


_TRANSITIONS = {
    ExperimentState.DRAFT: {ExperimentState.READY},
    ExperimentState.READY: {ExperimentState.DRAFT, ExperimentState.STARTING},
    ExperimentState.STARTING: {ExperimentState.RUNNING, ExperimentState.ABORTED},
    ExperimentState.RUNNING: {ExperimentState.STOPPING, ExperimentState.ABORTED},
    ExperimentState.STOPPING: {ExperimentState.COMPLETED, ExperimentState.ABORTED},
    ExperimentState.COMPLETED: set(),
    ExperimentState.ABORTED: set(),
}


def can_transition(current: ExperimentState, target: ExperimentState) -> bool:
    return target in _TRANSITIONS[current]
