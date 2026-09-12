"""ASGI integration coverage for authenticated device telemetry fanout."""

import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app

REPO_ROOT = Path(__file__).resolve().parents[3]
DEVICE_ID = "biovolt-01"
DEVICE_TOKEN = "integration-token-123"


def canonical_payload() -> dict[str, object]:
    """Load the canonical Phase 0 device payload for an end-to-end test."""

    return json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )


def make_app(tmp_path) -> object:
    """Create a fully lifespan-managed app backed by an isolated SQLite file."""

    return create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'integration.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )


def device_headers(token: str = DEVICE_TOKEN) -> dict[str, str]:
    return {
        "X-BioVolt-Device-ID": DEVICE_ID,
        "Authorization": f"Bearer {token}",
    }


def test_device_telemetry_reaches_dashboard_with_derived_values(tmp_path) -> None:
    """A valid device frame is processed, persisted, and broadcast to dashboards."""

    app = make_app(tmp_path)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers=device_headers(),
            ) as device:
                device.send_json(canonical_payload())
                processed = dashboard.receive_json()

    assert processed["schema_version"] == 1
    assert processed["device_id"] == DEVICE_ID
    assert processed["sequence"] == 1245
    assert processed["timestamp"].endswith("Z")
    assert processed["electrical"]["voltage_mv"] == pytest.approx(438.2)
    assert processed["electrical"]["current_ua"] == pytest.approx(4.382)
    assert processed["electrical"]["power_uw"] == pytest.approx(1.9201924)
    assert "bpv_adc_raw" not in processed
    assert "bpv_voltage_mv" not in processed
    assert "optical" not in processed

    latest = asyncio.run(app.state.telemetry_repository.latest(DEVICE_ID, "cell-a"))
    assert latest is not None
    assert latest.sequence == 1245


def test_malformed_device_frame_does_not_block_next_valid_broadcast(tmp_path) -> None:
    """A rejected frame returns an error while the authenticated socket stays usable."""

    app = make_app(tmp_path)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers=device_headers(),
            ) as device:
                device.send_text("not-json")
                assert device.receive_json() == {"error": "invalid telemetry frame"}

                device.send_json(canonical_payload())
                processed = dashboard.receive_json()

    assert processed["sequence"] == 1245
    assert processed["device_id"] == DEVICE_ID
    assert "error" not in processed


def test_wrong_device_token_is_closed_without_persisting(tmp_path) -> None:
    """Policy-rejected device authentication must not create a telemetry row."""

    app = make_app(tmp_path)

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as raised:
            with client.websocket_connect(
                "/ws/device",
                headers=device_headers("wrong-token-456"),
            ):
                pass
        assert raised.value.code == 1008

    rows = asyncio.run(app.state.telemetry_repository.history(DEVICE_ID, "cell-a", limit=10))
    assert rows == []
