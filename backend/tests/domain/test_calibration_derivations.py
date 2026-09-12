import pytest

from biovolt_backend.calibration.types import (
    BiomassCalibration,
    ElectricalCalibration,
    OpticalCalibration,
    ReactorCalibration,
)
from biovolt_backend.domain.biomass import derive_biomass, derive_carbon
from biovolt_backend.domain.calibrated_electrical import derive_electrical
from biovolt_backend.domain.optical_density import derive_od680


def test_electrical_preserves_negative_voltage_and_squared_power():
    result = derive_electrical(1, ElectricalCalibration(100, 2))
    assert result.corrected_voltage_mv == -1
    assert result.current_ua == -10
    assert result.power_uw == pytest.approx(0.01)


def test_od_ratio_and_invalid_sample():
    assert derive_od680(20, OpticalCalibration(10, 110)).od680 == pytest.approx(1)
    assert derive_od680(10, OpticalCalibration(10, 110)).reason == "nonpositive_corrected_sample"


def test_biomass_extrapolation_and_negative_carbon_delta():
    profile = BiomassCalibration("linear", 2, 0, 3, 1, 0, 0, 1)
    reactor = ReactorCalibration(2, 1.83)
    assert derive_biomass(2, profile, reactor).extrapolated
    carbon = derive_carbon(1, 3, reactor)
    assert carbon.biomass_delta_g == -2
    assert carbon.estimated_co2_biofixed_g == pytest.approx(-3.66)
    assert derive_carbon(1, None, reactor).eligible is False
