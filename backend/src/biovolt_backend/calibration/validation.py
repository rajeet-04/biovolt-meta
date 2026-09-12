import math
from dataclasses import dataclass, field

from .types import BiomassCalibration, ElectricalCalibration, OpticalCalibration, ReactorCalibration


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: dict[str, str] = field(default_factory=dict)


def validate_calibration(
    electrical: ElectricalCalibration | None = None,
    optical: OpticalCalibration | None = None,
    biomass: BiomassCalibration | None = None,
    reactor: ReactorCalibration | None = None,
) -> ValidationResult:
    errors: dict[str, str] = {}
    if electrical is not None:
        if not math.isfinite(electrical.load_resistance_ohm) or electrical.load_resistance_ohm <= 0:
            errors["load_resistance_ohm"] = "must be finite and greater than zero"
        if not math.isfinite(electrical.ads1115_offset_mv):
            errors["ads1115_offset_mv"] = "must be finite"
    if optical is not None:
        if not math.isfinite(optical.dark_raw):
            errors["dark_raw"] = "must be finite"
        if not math.isfinite(optical.blank_raw):
            errors["blank_raw"] = "must be finite"
        elif math.isfinite(optical.dark_raw) and optical.blank_raw <= optical.dark_raw:
            errors["blank_raw"] = "must be greater than dark_raw"
    if biomass is not None:
        if biomass.model_type != "linear":
            errors["model_type"] = "must be linear"
        if not math.isfinite(biomass.slope_g_l_per_od) or biomass.slope_g_l_per_od <= 0:
            errors["slope_g_l_per_od"] = "must be finite and greater than zero"
        if not math.isfinite(biomass.intercept_g_l):
            errors["intercept_g_l"] = "must be finite"
        if biomass.point_count < 3:
            errors["point_count"] = "must be at least three"
        if (
            not math.isfinite(biomass.od_min)
            or not math.isfinite(biomass.od_max)
            or biomass.od_min >= biomass.od_max
        ):
            errors["od_range"] = "must be finite with od_min less than od_max"
        for name, value in (("r_squared", biomass.r_squared), ("rmse_g_l", biomass.rmse_g_l)):
            if value is not None and not math.isfinite(value):
                errors[name] = "must be finite when provided"
    if reactor is not None:
        if not math.isfinite(reactor.reactor_volume_l) or reactor.reactor_volume_l <= 0:
            errors["reactor_volume_l"] = "must be finite and greater than zero"
        if (
            not math.isfinite(reactor.co2_per_dry_biomass_g_per_g)
            or reactor.co2_per_dry_biomass_g_per_g <= 0
        ):
            errors["co2_per_dry_biomass_g_per_g"] = "must be finite and greater than zero"
    return ValidationResult(not errors, errors)
