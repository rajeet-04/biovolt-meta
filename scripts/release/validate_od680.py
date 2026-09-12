import math


def recompute(sample: float, dark: float, blank: float) -> float | None:
    numerator, denominator = sample - dark, blank - dark
    if numerator <= 0 or denominator <= 0 or numerator / denominator <= 0:
        return None
    return -math.log10(numerator / denominator)
