from dataclasses import dataclass

from .types import AnalyticsSample


@dataclass(frozen=True)
class ScientificArmMetrics:
    starting_od680: float | None
    ending_od680: float | None
    od680_change: float | None
    starting_biomass_g_l: float | None
    ending_biomass_g_l: float | None
    biomass_concentration_change_g_l: float | None
    starting_dry_biomass_g: float | None
    ending_dry_biomass_g: float | None
    biomass_delta_g: float | None
    estimated_co2_biofixed_g: float | None


def summarize_scientific(samples: tuple[AnalyticsSample, ...]) -> ScientificArmMetrics:
    if not samples:
        return ScientificArmMetrics(None, None, None, None, None, None, None, None, None, None)
    first, last = samples[0], samples[-1]
    od = (
        (first.od680, last.od680, last.od680 - first.od680)
        if first.od680 is not None and last.od680 is not None
        else (None, None, None)
    )
    bio = (
        (first.biomass_g_l, last.biomass_g_l, last.biomass_g_l - first.biomass_g_l)
        if first.biomass_g_l is not None and last.biomass_g_l is not None
        else (None, None, None)
    )
    mass_delta = (
        last.dry_biomass_g - first.dry_biomass_g
        if first.dry_biomass_g is not None and last.dry_biomass_g is not None
        else None
    )
    return ScientificArmMetrics(
        *od, *bio, first.dry_biomass_g, last.dry_biomass_g, mass_delta, None
    )
