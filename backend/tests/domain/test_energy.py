import pytest

from biovolt_backend.domain.energy import EnergyAccumulator


def test_energy_uses_trapezoidal_integration() -> None:
    acc = EnergyAccumulator()

    assert acc.update("d1", "c1", 0, 10.0) == 0.0
    value = acc.update("d1", "c1", 1000, 20.0)

    assert value == pytest.approx(0.015)


def test_uptime_decrease_resets_boot_session_energy() -> None:
    acc = EnergyAccumulator()
    acc.update("d1", "c1", 1000, 10.0)
    acc.update("d1", "c1", 2000, 10.0)

    assert acc.update("d1", "c1", 100, 10.0) == 0.0


def test_duplicate_uptime_updates_power_without_adding_energy() -> None:
    acc = EnergyAccumulator()
    acc.update("d1", "c1", 0, 10.0)
    acc.update("d1", "c1", 1000, 10.0)

    assert acc.update("d1", "c1", 1000, 20.0) == pytest.approx(0.01)
    assert acc.update("d1", "c1", 2000, 20.0) == pytest.approx(0.03)


def test_none_power_gaps_advance_state_without_adding_energy() -> None:
    acc = EnergyAccumulator()
    acc.update("d1", "c1", 0, 10.0)

    assert acc.update("d1", "c1", 1000, None) == 0.0
    assert acc.update("d1", "c1", 2000, 20.0) == 0.0
    assert acc.update("d1", "c1", 3000, 20.0) == pytest.approx(0.02)


def test_reset_discards_state_for_one_cell() -> None:
    acc = EnergyAccumulator()
    acc.update("d1", "c1", 0, 10.0)
    acc.update("d1", "c1", 1000, 10.0)
    acc.reset("d1", "c1")

    assert acc.update("d1", "c1", 2000, 10.0) == 0.0
    assert acc.update("d1", "c2", 1000, 10.0) == 0.0


def test_energy_overflow_is_atomic_and_does_not_poison_prior_state() -> None:
    acc = EnergyAccumulator()
    acc.update("d1", "c1", 0, 1e303)

    with pytest.raises(OverflowError, match="cumulative energy overflow"):
        acc.update("d1", "c1", 2**63 - 1, 1e303)

    assert acc.update("d1", "c1", 1000, 1e303) == pytest.approx(1e300)
