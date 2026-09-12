"""Optical calculations for biophotovoltaic telemetry."""

import math


def calculate_od680(
    sample_raw: float | None,
    dark_raw: float | None,
    blank_raw: float | None,
) -> float | None:
    """Calculate dark- and blank-corrected optical density at 680 nm."""
    if sample_raw is None or dark_raw is None or blank_raw is None:
        return None
    numerator = sample_raw - dark_raw
    denominator = blank_raw - dark_raw
    if numerator <= 0 or denominator <= 0:
        return None
    return -math.log10(numerator / denominator)
