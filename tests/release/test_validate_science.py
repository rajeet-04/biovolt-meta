import pytest

from scripts.release.validate_biomass_carbon import estimate
from scripts.release.validate_electrical import recompute
from scripts.release.validate_energy import integrate
from scripts.release.validate_od680 import recompute as od680


def test_electrical_reference():
    current, power = recompute(438.2, 100000)
    assert current == pytest.approx(4.382)
    assert power == pytest.approx(1.9201924)


def test_energy_skips_large_gap_and_reboot():
    assert integrate([(0, 10), (1000, 20), (5000, 20), (100, 20)]) == pytest.approx(0.015)


def test_od680_reference_and_invalid_domain():
    assert od680(20, 10, 110) == pytest.approx(1)
    assert od680(10, 10, 110) is None


def test_biomass_requires_measured_provenance():
    assert estimate(1, 2, 0, 1, 0, "synthetic_demo")["eligible"] is False
    assert estimate(1, 2, 0, 1, 0, "measured")["estimated_co2_biofixed_g"] == pytest.approx(3.66)
