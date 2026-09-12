"""Fan out processed telemetry to read-only dashboard WebSocket clients."""

import asyncio
from threading import RLock
from typing import Any


class DashboardHub:
    """Maintain dashboard connections and isolate individual send failures."""

    def __init__(self, *, send_timeout_seconds: float = 1.0) -> None:
        self._connections: set[Any] = set()
        self._lock = RLock()
        self._send_timeout_seconds = send_timeout_seconds

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

        await asyncio.gather(
            *(self._send_one(websocket, payload) for websocket in connections),
        )

    async def _send_one(self, websocket: Any, payload: dict[str, object]) -> None:
        try:
            await asyncio.wait_for(
                websocket.send_json(payload),
                timeout=self._send_timeout_seconds,
            )
        except Exception:
            self.disconnect(websocket)
