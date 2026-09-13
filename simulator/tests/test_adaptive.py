import pytest

from biovolt_simulator.adaptive import AdaptiveConfig, SyntheticAdaptive


def test_config_rejects_unsafe_bounds():
    with pytest.raises(ValueError):
        AdaptiveConfig(pwm_min=100, pwm_max=10).validate()


def test_synthetic_trace_reverses_on_worse_objective_and_stays_bounded():
    controller = SyntheticAdaptive(AdaptiveConfig(initial_pwm=8, pwm_min=4, pwm_max=16, pwm_step=4))
    first, direction = controller.update([10, 10, 10])
    assert (first, direction) == (12, 1)
    second, direction = controller.update([9, 9, 9])
    assert (second, direction) == (8, -1)
    assert 4 <= second <= 16


def test_simulator_behavior_is_explicitly_synthetic():
    assert SyntheticAdaptive.__doc__ and "synthetic" in SyntheticAdaptive.__doc__.lower()
