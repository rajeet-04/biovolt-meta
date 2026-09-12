import pytest

from biovolt_backend.domain.electrical import current_ua, power_uw


def test_current_conversion_uses_mv_and_ohms():
    assert current_ua(438.2, 100_000.0) == pytest.approx(4.382)


def test_power_conversion_returns_microwatts():
    assert power_uw(438.2, 100_000.0) == pytest.approx(1.9201924)


def test_non_positive_resistance_is_rejected():
    with pytest.raises(ValueError):
        current_ua(438.2, 0)
