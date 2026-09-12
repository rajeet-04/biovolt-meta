"""Electrical calculations for biophotovoltaic telemetry."""


def _validate_resistance(resistance_ohm: float) -> None:
    if resistance_ohm <= 0:
        raise ValueError("resistance_ohm must be > 0")


def current_ua(voltage_mv: float, resistance_ohm: float) -> float:
    """Return current in microamps for millivolts and ohms."""
    _validate_resistance(resistance_ohm)
    return voltage_mv * 1000.0 / resistance_ohm


def power_uw(voltage_mv: float, resistance_ohm: float) -> float:
    """Return power in microwatts for millivolts and ohms."""
    _validate_resistance(resistance_ohm)
    return voltage_mv**2 / resistance_ohm
