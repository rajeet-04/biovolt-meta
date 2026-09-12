"""Authenticated WebSocket transport for simulator telemetry."""

from __future__ import annotations

import asyncio
import json
from time import monotonic
from typing import Protocol

import websockets

from .config import SimulatorSettings
from .generator import TelemetryGenerator

_MAX_RECONNECT_DELAY_SECONDS = 10.0


class _FrameGenerator(Protocol):
    def next_frame(self, elapsed_seconds: float) -> dict[str, object]: ...


def device_headers(settings: SimulatorSettings) -> dict[str, str]:
    """Build the authenticated device headers for a WebSocket connection."""

    return {
        "X-BioVolt-Device-ID": settings.device_id,
        "Authorization": f"Bearer {settings.device_token}",
    }


def reconnect_delay(attempt: int) -> float:
    """Return bounded exponential backoff for a zero-based reconnect attempt."""

    return min(_MAX_RECONNECT_DELAY_SECONDS, 2.0 ** max(0, attempt))


class SimulatorClient:
    """Send generated raw telemetry to the backend device WebSocket."""

    def __init__(
        self,
        settings: SimulatorSettings,
        *,
        generator: _FrameGenerator | None = None,
    ) -> None:
        self.settings = settings
        self.generator = generator or TelemetryGenerator(
            seed=settings.seed,
            device_id=settings.device_id,
            cell_id=settings.cell_id,
            start_sequence=settings.start_sequence,
        )

    async def run(self) -> None:
        """Connect, send at cadence, and reconnect on transport errors."""

        headers = device_headers(self.settings)
        attempt = 0
        started = monotonic()

        while True:
            try:
                async with websockets.connect(
                    self.settings.backend_ws_url,
                    additional_headers=headers,
                ) as websocket:
                    attempt = 0
                    while True:
                        elapsed = monotonic() - started
                        frame = self.generator.next_frame(elapsed)
                        await websocket.send(json.dumps(frame))
                        await asyncio.sleep(self.settings.interval_seconds)
            except asyncio.CancelledError:
                raise
            except (OSError, websockets.WebSocketException):
                await asyncio.sleep(reconnect_delay(attempt))
                attempt += 1
