import pytest

from biovolt_backend.experiments.state import ExperimentState, can_transition


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ExperimentState.DRAFT, ExperimentState.READY),
        (ExperimentState.READY, ExperimentState.DRAFT),
        (ExperimentState.READY, ExperimentState.STARTING),
        (ExperimentState.STARTING, ExperimentState.RUNNING),
        (ExperimentState.RUNNING, ExperimentState.STOPPING),
        (ExperimentState.STOPPING, ExperimentState.COMPLETED),
    ],
)
def test_allowed_transitions(current: ExperimentState, target: ExperimentState) -> None:
    assert can_transition(current, target)


@pytest.mark.parametrize("state", [ExperimentState.COMPLETED, ExperimentState.ABORTED])
def test_terminal_states_cannot_transition(state: ExperimentState) -> None:
    assert not can_transition(state, ExperimentState.DRAFT)
