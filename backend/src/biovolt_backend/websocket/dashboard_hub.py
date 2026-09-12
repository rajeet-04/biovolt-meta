"""Fan out processed telemetry to read-only dashboard WebSocket clients."""

import asyncio
import inspect
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

    def broadcast_json(self, payload: dict[str, object]) -> None:
        """Send a payload to every dashboard, removing failed connections.

        FastAPI's ``send_json`` is asynchronous, while small fakes used by
        status/tests may be synchronous.  Both forms are supported; async
        sends are scheduled on the current event loop.
        """

        with self._lock:
            connections = tuple(self._connections)

        for websocket in connections:
            try:
                result = websocket.send_json(payload)
            except Exception:
                self.disconnect(websocket)
                continue
            if inspect.isawaitable(result):
                self._schedule_send(websocket, result)

    def _schedule_send(self, websocket: Any, result: Any) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._finish_send(websocket, result))
        else:
            loop.create_task(self._finish_send(websocket, result))

    async def _finish_send(self, websocket: Any, result: Any) -> None:
        try:
            await result
        except Exception:
            self.disconnect(websocket)
