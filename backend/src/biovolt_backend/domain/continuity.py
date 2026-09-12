"""Source-neutral telemetry sequence continuity tracking."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ContinuityResult:
    contiguous: bool
    restarted: bool


class TelemetryContinuityTracker:
    """Track accepted telemetry sequence and uptime for each device/cell."""

    def __init__(self) -> None:
        self._last: dict[tuple[str, str], tuple[int, int]] = {}

    def observe(
        self,
        device_id: str,
        cell_id: str,
        sequence: int,
        uptime_ms: int,
        *,
        commit: bool = True,
    ) -> ContinuityResult:
        key = (device_id, cell_id)
        previous = self._last.get(key)
        if previous is None:
            if commit:
                self._last[key] = (sequence, uptime_ms)
            return ContinuityResult(contiguous=False, restarted=False)

        previous_sequence, previous_uptime = previous
        if uptime_ms < previous_uptime:
            if commit:
                self._last[key] = (sequence, uptime_ms)
            return ContinuityResult(contiguous=False, restarted=True)
        if sequence <= previous_sequence:
            return ContinuityResult(contiguous=False, restarted=False)

        if commit:
            self._last[key] = (sequence, uptime_ms)
        return ContinuityResult(
            contiguous=sequence == previous_sequence + 1,
            restarted=False,
        )

    def reset(self, device_id: str, cell_id: str) -> None:
        self._last.pop((device_id, cell_id), None)
