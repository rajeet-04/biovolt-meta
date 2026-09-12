from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class ElectricalCalibration:
    load_resistance_ohm: float
    ads1115_offset_mv: float


@dataclass(frozen=True)
class OpticalCalibration:
    dark_raw: float
    blank_raw: float


@dataclass(frozen=True)
class BiomassCalibration:
    model_type: Literal["linear"]
    slope_g_l_per_od: float
    intercept_g_l: float
    point_count: int
    r_squared: float | None
    rmse_g_l: float | None
    od_min: float
    od_max: float


@dataclass(frozen=True)
class ReactorCalibration:
    reactor_volume_l: float
    co2_per_dry_biomass_g_per_g: float
