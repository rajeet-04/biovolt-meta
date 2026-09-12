import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BiomassCalibrationPoint:
    od680: float
    dry_biomass_g_l: float


@dataclass(frozen=True)
class LinearFitResult:
    slope_g_l_per_od: float
    intercept_g_l: float
    r_squared: float | None
    rmse_g_l: float
    point_count: int
    unique_od_count: int
    od_min: float
    od_max: float


def fit_linear_biomass(points: Sequence[BiomassCalibrationPoint]) -> LinearFitResult:
    if len(points) < 3:
        raise ValueError("at least three calibration points are required")
    if any(
        not math.isfinite(p.od680) or not math.isfinite(p.dry_biomass_g_l) or p.dry_biomass_g_l < 0
        for p in points
    ):
        raise ValueError("calibration points must be finite with non-negative biomass")
    unique = len({p.od680 for p in points})
    if unique < 3:
        raise ValueError("at least three distinct OD values are required")
    xbar = sum(p.od680 for p in points) / len(points)
    ybar = sum(p.dry_biomass_g_l for p in points) / len(points)
    sxx = sum((p.od680 - xbar) ** 2 for p in points)
    if sxx == 0:
        raise ValueError("OD variance must be non-zero")
    slope = sum((p.od680 - xbar) * (p.dry_biomass_g_l - ybar) for p in points) / sxx
    if not math.isfinite(slope) or slope <= 0:
        raise ValueError("fit slope must be finite and greater than zero")
    intercept = ybar - slope * xbar
    residuals = [p.dry_biomass_g_l - (slope * p.od680 + intercept) for p in points]
    ss_res = sum(r * r for r in residuals)
    ss_tot = sum((p.dry_biomass_g_l - ybar) ** 2 for p in points)
    r_squared = None if ss_tot == 0 else 1 - ss_res / ss_tot
    return LinearFitResult(
        slope,
        intercept,
        r_squared,
        math.sqrt(ss_res / len(points)),
        len(points),
        unique,
        min(p.od680 for p in points),
        max(p.od680 for p in points),
    )
