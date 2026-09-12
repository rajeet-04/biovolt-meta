"""ASGI integration coverage for live broadcast and persistence cadence."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
DEVICE_ID = "biovolt-01"
DEVICE_TOKEN = "integration-token-123"
BASE_TIMESTAMP = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)


def canonical_payload() -> dict[str, object]:
    """Load a fresh canonical frame so each send can change its counters."""

    return json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )


class TimestampedTelemetryService:
    """Inject deterministic receive timestamps while retaining the real service."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate

    async def handle_raw(self, payload, authenticated_device_id, received_at):
        del received_at
        frame_index = int(payload["sequence"]) - 1245
        timestamp = BASE_TIMESTAMP + timedelta(seconds=frame_index * 0.5)
        return await self._delegate.handle_raw(payload, authenticated_device_id, timestamp)


def test_five_live_frames_persist_at_one_hz(tmp_path) -> None:
    """Five 500 ms frames broadcast live while throttle persists frames at 0/1/2 s."""

    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'cadence.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )

    with TestClient(app) as client:
        app.state.telemetry_service = TimestampedTelemetryService(app.state.telemetry_service)
        live_sequences: list[int] = []
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                for frame_index in range(5):
                    payload = canonical_payload()
                    payload["sequence"] = 1245 + frame_index
                    payload["uptime_ms"] = 1000 + frame_index * 500
                    device.send_json(payload)
                    live_sequences.append(dashboard.receive_json()["sequence"])

    rows = asyncio.run(app.state.telemetry_repository.history(DEVICE_ID, "cell-a", limit=10))
    assert live_sequences == [1245, 1246, 1247, 1248, 1249]
    assert [row.sequence for row in rows] == [1245, 1247, 1249]
    assert len(rows) == 3
    assert [row.received_at for row in rows] == [
        BASE_TIMESTAMP,
        BASE_TIMESTAMP + timedelta(seconds=1),
        BASE_TIMESTAMP + timedelta(seconds=2),
    ]
