"""Cadence control for per-cell telemetry persistence."""

from datetime import datetime


class PersistenceThrottle:
    """Allow persistence at most once per configured interval per cell."""

    def __init__(self, interval_seconds: float = 1.0) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be > 0")
        self.interval_seconds = interval_seconds
        self._last_persisted: dict[tuple[str, str], datetime] = {}

    def should_persist(self, device_id: str, cell_id: str, timestamp: datetime) -> bool:
        key = (device_id, cell_id)
        previous = self._last_persisted.get(key)
        if previous is not None and (timestamp - previous).total_seconds() < self.interval_seconds:
            return False
        self._last_persisted[key] = timestamp
        return True
