import math
from dataclasses import dataclass

from biovolt_backend.calibration.types import ElectricalCalibration


@dataclass(frozen=True)
class ElectricalResult:
    corrected_voltage_mv: float | None
    current_ua: float | None
    power_uw: float | None
    eligible: bool
    reason: str | None


def derive_electrical(
    measured_voltage_mv: float | None, calibration: ElectricalCalibration | None
) -> ElectricalResult:
    if measured_voltage_mv is None:
        return ElectricalResult(None, None, None, False, "missing_voltage")
    if calibration is None:
        return ElectricalResult(None, None, None, False, "missing_calibration")
    if not math.isfinite(measured_voltage_mv):
        return ElectricalResult(None, None, None, False, "invalid_voltage")
    corrected = measured_voltage_mv - calibration.ads1115_offset_mv
    current = corrected * 1000 / calibration.load_resistance_ohm
    power = corrected * corrected / calibration.load_resistance_ohm
    return ElectricalResult(corrected, current, power, True, None)
