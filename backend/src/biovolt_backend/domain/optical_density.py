import math
from dataclasses import dataclass

from biovolt_backend.calibration.types import OpticalCalibration


@dataclass(frozen=True)
class OdResult:
    od680: float | None
    transmission_ratio: float | None
    eligible: bool
    reason: str | None


def derive_od680(sample_raw: float | None, calibration: OpticalCalibration | None) -> OdResult:
    if sample_raw is None:
        return OdResult(None, None, False, "missing_sample")
    if calibration is None:
        return OdResult(None, None, False, "missing_calibration")
    denominator = calibration.blank_raw - calibration.dark_raw
    corrected_sample = sample_raw - calibration.dark_raw
    if not math.isfinite(denominator) or denominator <= 0:
        return OdResult(None, None, False, "invalid_blank_dark")
    if not math.isfinite(corrected_sample) or corrected_sample <= 0:
        return OdResult(None, None, False, "nonpositive_corrected_sample")
    ratio = corrected_sample / denominator
    if not math.isfinite(ratio) or ratio <= 0:
        return OdResult(None, ratio, False, "invalid_transmission")
    return OdResult(-math.log10(ratio), ratio, True, None)
