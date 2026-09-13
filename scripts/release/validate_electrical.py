from math import isfinite


def recompute(voltage_mv: float, resistance_ohm: float) -> tuple[float, float]:
    if not isfinite(voltage_mv) or not isfinite(resistance_ohm) or resistance_ohm <= 0:
        raise ValueError("finite voltage and positive resistance required")
    return voltage_mv * 1000 / resistance_ohm, voltage_mv * voltage_mv / resistance_ohm
