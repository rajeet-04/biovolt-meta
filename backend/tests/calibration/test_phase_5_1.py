import pytest

from biovolt_backend.calibration.biomass_fit import BiomassCalibrationPoint, fit_linear_biomass
from biovolt_backend.calibration.types import (
    BiomassCalibration,
    ElectricalCalibration,
    OpticalCalibration,
    ReactorCalibration,
)
from biovolt_backend.calibration.validation import validate_calibration


def test_valid_profile_and_validation_boundaries():
    result = validate_calibration(
        ElectricalCalibration(1000, 2),
        OpticalCalibration(10, 110),
        BiomassCalibration("linear", 2, 0, 3, 1, 0, 0, 2),
        ReactorCalibration(1, 1.83),
    )
    assert result.valid
    assert (
        "load_resistance_ohm" in validate_calibration(electrical=ElectricalCalibration(0, 0)).errors
    )


def test_linear_fit_requires_points_and_reports_diagnostics():
    fit = fit_linear_biomass(
        [
            BiomassCalibrationPoint(0.1, 0.2),
            BiomassCalibrationPoint(0.5, 1.0),
            BiomassCalibrationPoint(1.0, 2.0),
        ]
    )
    assert fit.slope_g_l_per_od == pytest.approx(2)
    assert fit.intercept_g_l == pytest.approx(0)
    assert fit.r_squared == pytest.approx(1)
    with pytest.raises(ValueError):
        fit_linear_biomass(
            [
                BiomassCalibrationPoint(0, 1),
                BiomassCalibrationPoint(0, 2),
                BiomassCalibrationPoint(0, 3),
            ]
        )
