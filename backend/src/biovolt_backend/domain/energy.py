"""Boot-session energy accumulation for telemetry samples."""

import math
from dataclasses import dataclass


@dataclass
class _EnergyState:
    uptime_ms: int
    power_uw: float | None
    cumulative_mj: float


class EnergyAccumulator:
    """Integrate per-cell power while preserving boot-session boundaries."""

    def __init__(self) -> None:
        self._states: dict[tuple[str, str], _EnergyState] = {}

    def update(
        self,
        device_id: str,
        cell_id: str,
        uptime_ms: int,
        power_uw: float | None,
    ) -> float:
        key = (device_id, cell_id)
        previous = self._states.get(key)
        if previous is None or uptime_ms < previous.uptime_ms:
            self._states[key] = _EnergyState(uptime_ms, power_uw, 0.0)
            return 0.0

        cumulative_mj = previous.cumulative_mj
        if (
            uptime_ms > previous.uptime_ms
            and previous.power_uw is not None
            and power_uw is not None
        ):
            try:
                elapsed_s = (uptime_ms - previous.uptime_ms) / 1000.0
                average_power_uw = (previous.power_uw + power_uw) / 2.0
                cumulative_mj += average_power_uw * elapsed_s / 1000.0
            except OverflowError as exc:
                raise OverflowError("cumulative energy overflow") from exc
            if not math.isfinite(cumulative_mj):
                raise OverflowError("cumulative energy overflow")

        self._states[key] = _EnergyState(uptime_ms, power_uw, cumulative_mj)
        return cumulative_mj

    def reset(self, device_id: str, cell_id: str) -> None:
        self._states.pop((device_id, cell_id), None)
