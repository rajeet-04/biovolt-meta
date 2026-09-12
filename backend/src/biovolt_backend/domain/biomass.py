from dataclasses import dataclass

from biovolt_backend.calibration.types import BiomassCalibration, ReactorCalibration


@dataclass(frozen=True)
class BiomassResult:
    biomass_g_l: float | None
    dry_biomass_g: float | None
    extrapolated: bool
    eligible: bool
    reason: str | None


@dataclass(frozen=True)
class CarbonResult:
    biomass_delta_g: float | None
    estimated_co2_biofixed_g: float | None
    eligible: bool
    reason: str | None


def derive_biomass(
    od680: float | None,
    calibration: BiomassCalibration | None,
    reactor: ReactorCalibration | None = None,
) -> BiomassResult:
    if od680 is None:
        return BiomassResult(None, None, False, False, "missing_od680")
    if calibration is None:
        return BiomassResult(None, None, False, False, "missing_calibration")
    biomass = calibration.slope_g_l_per_od * od680 + calibration.intercept_g_l
    extrapolated = od680 < calibration.od_min or od680 > calibration.od_max
    dry_mass = None if reactor is None else biomass * reactor.reactor_volume_l
    return BiomassResult(biomass, dry_mass, extrapolated, True, None)


def derive_carbon(
    current_dry_biomass_g: float | None,
    baseline_dry_biomass_g: float | None,
    reactor: ReactorCalibration | None,
) -> CarbonResult:
    if current_dry_biomass_g is None or baseline_dry_biomass_g is None:
        return CarbonResult(None, None, False, "missing_baseline")
    if reactor is None:
        return CarbonResult(None, None, False, "missing_calibration")
    delta = current_dry_biomass_g - baseline_dry_biomass_g
    return CarbonResult(delta, delta * reactor.co2_per_dry_biomass_g_per_g, True, None)
