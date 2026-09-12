"""Prove any authenticated Phase 0 device can use the telemetry boundary."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.domain.electrical import power_uw
from biovolt_backend.domain.optical import calculate_od680
from biovolt_backend.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
DEVICE_ID = "biovolt-hw-test-01"
DEVICE_TOKEN = "integration-token-123"
BASE_TIMESTAMP = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)


def canonical_payload() -> dict[str, object]:
    """Load the canonical Phase 0 frame without simulator-specific helpers."""

    return json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )


class TimestampedTelemetryService:
    """Keep receive times deterministic while using the real service pipeline."""

    def __init__(self, delegate) -> None:
        self._delegate = delegate

    async def handle_raw(self, payload, authenticated_device_id, received_at):
        del received_at
        frame_index = int(payload["sequence"]) - 1245
        timestamp = BASE_TIMESTAMP + timedelta(seconds=frame_index * 0.5)
        return await self._delegate.handle_raw(payload, authenticated_device_id, timestamp)


def test_hardware_like_device_has_full_telemetry_pipeline_parity(tmp_path) -> None:
    """A generic device ID gets the same processing, persistence, and fanout path."""

    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'parity.db'}",
            device_shared_token=DEVICE_TOKEN,
            load_resistance_ohm=100_000.0,
            bpw34_dark_raw=320,
            bpw34_blank_raw=23_840,
        )
    )

    with TestClient(app) as client:
        app.state.telemetry_service = TimestampedTelemetryService(app.state.telemetry_service)
        processed_frames: list[dict[str, object]] = []
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                for frame_index in range(3):
                    payload = canonical_payload()
                    payload["device_id"] = DEVICE_ID
                    payload["sequence"] = 1245 + frame_index
                    payload["uptime_ms"] = 582_340 + frame_index * 500
                    device.send_json(payload)
                    processed_frames.append(dashboard.receive_json())

                status_response = client.get("/api/system/status")
                latest_response = client.get(
                    "/api/telemetry/latest",
                    params={"device_id": DEVICE_ID, "cell_id": "cell-a"},
                )

    assert [frame["device_id"] for frame in processed_frames] == [DEVICE_ID] * 3
    assert [frame["sequence"] for frame in processed_frames] == [1245, 1246, 1247]
    latest_live = processed_frames[-1]
    assert latest_live["electrical"]["current_ua"] == pytest.approx(4.382)
    assert latest_live["electrical"]["power_uw"] == pytest.approx(power_uw(438.2, 100_000.0))
    assert latest_live["biological"]["od680"] == pytest.approx(calculate_od680(17_320, 320, 23_840))
    expected_power = power_uw(438.2, 100_000.0)
    assert [frame["electrical"]["cumulative_energy_mj"] for frame in processed_frames] == [
        pytest.approx(0.0),
        pytest.approx(expected_power * 0.5 / 1000.0),
        pytest.approx(expected_power * 1.0 / 1000.0),
    ]

    assert status_response.status_code == 200
    status = status_response.json()
    assert status["connected_devices"] == [DEVICE_ID]
    assert status["device_count"] == 1
    assert status["devices"][DEVICE_ID]["latest_telemetry_at"].endswith("Z")

    assert latest_response.status_code == 200
    latest = latest_response.json()
    validate_payload("processed-telemetry.v1.schema.json", latest)
    assert latest["device_id"] == DEVICE_ID
    assert latest["sequence"] == 1247
    assert latest["electrical"]["cumulative_energy_mj"] == pytest.approx(expected_power / 1000.0)
    assert latest["biological"]["od680"] == pytest.approx(calculate_od680(17_320, 320, 23_840))

    rows = asyncio.run(app.state.telemetry_repository.history(DEVICE_ID, "cell-a", limit=10))
    assert [row.sequence for row in rows] == [1245, 1247]
