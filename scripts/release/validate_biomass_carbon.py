def estimate(
    od680: float | None,
    slope: float | None,
    intercept: float | None,
    volume_l: float | None,
    baseline_g: float | None,
    evidence_class: str,
) -> dict[str, float | None | bool]:
    valid = (
        all(value is not None for value in (od680, slope, intercept, volume_l, baseline_g))
        and volume_l is not None
        and volume_l > 0
        and evidence_class == "measured"
    )
    biomass = (slope * od680 + intercept) if valid else None
    total = biomass * volume_l if biomass is not None and volume_l is not None else None
    delta = total - baseline_g if total is not None and baseline_g is not None else None
    return {
        "eligible": valid,
        "biomass_g_l": biomass,
        "biomass_delta_g": delta,
        "estimated_co2_biofixed_g": delta * 1.83 if delta is not None else None,
    }
