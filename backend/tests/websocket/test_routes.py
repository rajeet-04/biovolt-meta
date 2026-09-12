import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from biovolt_backend.config import Settings
from biovolt_backend.domain.energy import EnergyAccumulator
from biovolt_backend.domain.processing import ProcessingConfig
from biovolt_backend.main import create_app
from biovolt_backend.persistence.throttle import PersistenceThrottle
from biovolt_backend.services.telemetry_service import TelemetryService

REPO_ROOT = Path(__file__).resolve().parents[3]
DEVICE_TOKEN = "test-token-123"
DEVICE_ID = "biovolt-01"


def canonical_payload() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )


def test_unauthenticated_device_socket_closes_with_policy_violation(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )

    with TestClient(app) as client:
        with pytest.raises(WebSocketDisconnect) as raised:
            with client.websocket_connect("/ws/device"):
                pass

    assert raised.value.code == 1008


def test_authenticated_device_telemetry_is_processed_and_persisted(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                device.send_json(canonical_payload())
                assert dashboard.receive_json()["sequence"] == 1245

        latest = asyncio.run(client.app.state.telemetry_repository.latest(DEVICE_ID, "cell-a"))

    assert latest is not None
    assert latest.sequence == 1245
    assert app.state.device_registry.latest_telemetry_at(DEVICE_ID) is not None


def test_dashboard_receives_processed_telemetry_with_derived_fields(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                device.send_json(canonical_payload())
                processed = dashboard.receive_json()

    assert processed["device_id"] == DEVICE_ID
    assert processed["electrical"]["current_ua"] == pytest.approx(4.382)
    assert processed["electrical"]["power_uw"] == pytest.approx(1.9201924)
    assert processed["timestamp"].endswith("Z")


def test_malformed_device_frame_returns_error_and_connection_continues(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                device.send_text("not-json")
                assert device.receive_json() == {"error": "invalid telemetry frame"}

                device.send_json(canonical_payload())
                assert dashboard.receive_json()["sequence"] == 1245


def test_overflowing_device_frame_returns_error_and_connection_continues(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    overflowing = canonical_payload()
    overflowing["electrical"]["bpv_voltage_mv"] = 1e200  # type: ignore[index]

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                device.send_json(overflowing)
                assert device.receive_json() == {"error": "invalid telemetry frame"}

                device.send_json(canonical_payload())
                assert dashboard.receive_json()["sequence"] == 1245


def test_storage_unsafe_integer_frame_returns_error_and_connection_continues(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    unsafe_frames = []
    for field, unsafe_value in (("uptime_ms", 10**1000), ("sequence", 10**100)):
        payload = canonical_payload()
        payload[field] = unsafe_value
        unsafe_frames.append(payload)

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                for payload in unsafe_frames:
                    device.send_json(payload)
                    assert device.receive_json() == {"error": "invalid telemetry frame"}

                device.send_json(canonical_payload())
                assert dashboard.receive_json()["sequence"] == 1245


def test_non_finite_derived_electrical_frame_returns_error_and_continues(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    overflowing = canonical_payload()
    overflowing["electrical"]["bpv_voltage_mv"] = 1.0  # type: ignore[index]

    with TestClient(app) as client:
        app.state.telemetry_service = TelemetryService(
            config=ProcessingConfig(
                load_resistance_ohm=1e-306,
                bpw34_dark_raw=320,
                bpw34_blank_raw=23_840,
            ),
            energy=EnergyAccumulator(),
            throttle=PersistenceThrottle(),
            repository=app.state.telemetry_repository,
            dashboard_hub=app.state.dashboard_hub,
            device_registry=app.state.device_registry,
        )
        with client.websocket_connect("/ws/dashboard") as dashboard:
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                device.send_json(overflowing)
                assert device.receive_json() == {"error": "invalid telemetry frame"}

                valid = canonical_payload()
                valid["electrical"]["bpv_voltage_mv"] = 0.0  # type: ignore[index]
                device.send_json(valid)
                assert dashboard.receive_json()["sequence"] == 1245


def test_dashboard_is_read_only_and_ignores_client_commands(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'routes.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )

    with TestClient(app) as client:
        with client.websocket_connect("/ws/dashboard") as dashboard:
            dashboard.send_json({"command": "set_pwm", "value": 255})
            with client.websocket_connect(
                "/ws/device",
                headers={
                    "X-BioVolt-Device-ID": DEVICE_ID,
                    "Authorization": f"Bearer {DEVICE_TOKEN}",
                },
            ) as device:
                device.send_json(canonical_payload())
                telemetry = dashboard.receive_json()

    assert telemetry["device_id"] == DEVICE_ID
    assert telemetry["actuators"]["grow_led_pwm"] == 130
