"""Fan out processed telemetry to read-only dashboard WebSocket clients."""

from threading import RLock
from typing import Any


class DashboardHub:
    """Maintain dashboard connections and isolate individual send failures."""

    def __init__(self) -> None:
        self._connections: set[Any] = set()
        self._lock = RLock()

    def connect(self, websocket: Any) -> None:
        """Add a dashboard socket to the broadcast set."""

        with self._lock:
            self._connections.add(websocket)

    def disconnect(self, websocket: Any) -> None:
        """Remove a dashboard socket if present."""

        with self._lock:
            self._connections.discard(websocket)

    async def broadcast_json(self, payload: dict[str, object]) -> None:
        """Send a payload to every dashboard before returning.

        Each socket is handled independently so one closed dashboard cannot
        prevent healthy clients from receiving telemetry.  The connection
        snapshot is taken under the lock, but sends happen after releasing it.
        """

        with self._lock:
            connections = tuple(self._connections)

        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(websocket)
