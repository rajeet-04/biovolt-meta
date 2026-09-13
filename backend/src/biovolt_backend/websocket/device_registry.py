"""In-memory registry of authenticated device WebSocket connections."""

import asyncio
from datetime import datetime
from threading import RLock
from typing import Any


class DeviceRegistry:
    """Track the active socket and most recent telemetry time per device.

    State changes are short, atomic operations.  The registry does not await
    while holding its lock, so it is safe to use from the event loop and from
    synchronous test or status callers alike.
    """

    def __init__(self) -> None:
        self._connections: dict[str, Any] = {}
        self._send_locks: dict[str, asyncio.Lock] = {}
        self._latest_telemetry: dict[str, datetime] = {}
        self._lock = RLock()

    def connect(self, device_id: str, websocket: Any) -> None:
        """Register ``websocket`` as the active connection for ``device_id``."""

        with self._lock:
            self._connections[device_id] = websocket
            self._send_locks[device_id] = asyncio.Lock()

    def disconnect(self, device_id: str, websocket: Any) -> None:
        """Remove a socket only when it is still the active device socket."""

        with self._lock:
            if self._connections.get(device_id) is websocket:
                del self._connections[device_id]
                self._send_locks.pop(device_id, None)

    async def send_json(self, device_id: str, payload: dict[str, object]) -> bool:
        """Send one payload if the device is connected, without blocking reconnects."""

        with self._lock:
            websocket = self._connections.get(device_id)
            lock = self._send_locks.get(device_id)
        if websocket is None or lock is None:
            return False
        try:
            async with lock:
                await websocket.send_json(payload)
        except Exception:
            self.disconnect(device_id, websocket)
            return False
        return True

    def connected_device_ids(self) -> list[str]:
        """Return a stable snapshot of currently connected device IDs."""

        with self._lock:
            return list(self._connections)

    def mark_telemetry(self, device_id: str, received_at: datetime) -> None:
        """Record the server receive time for the latest device telemetry."""

        with self._lock:
            self._latest_telemetry[device_id] = received_at

    def latest_telemetry_at(self, device_id: str) -> datetime | None:
        """Return the latest server receive time, if telemetry was received."""

        with self._lock:
            return self._latest_telemetry.get(device_id)
