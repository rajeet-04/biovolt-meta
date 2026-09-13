import json
import time

from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app

DEVICE_TOKEN = "test-token-123"


def test_acknowledgements_drive_experiment_running_and_reject_mismatched_device(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'ack.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/experiments",
            json={
                "name": "Acked run",
                "arms": [
                    {
                        "device_id": "biovolt-01",
                        "cell_id": "cell-a",
                        "mode": "manual",
                        "initial_led_pwm": 96,
                    }
                ],
            },
        ).json()
        experiment_id = created["id"]
        assert client.post(f"/api/experiments/{experiment_id}/ready").status_code == 200
        with client.websocket_connect(
            "/ws/device",
            headers={
                "X-BioVolt-Device-ID": "biovolt-01",
                "Authorization": f"Bearer {DEVICE_TOKEN}",
            },
        ) as device:
            assert (
                client.post(f"/api/experiments/{experiment_id}/start").json()["state"] == "starting"
            )
            commands = [device.receive_json(), device.receive_json()]
            assert {command["kind"] for command in commands} == {"set_mode", "set_led_pwm"}

            for command in commands:
                device.send_json(
                    {
                        "schema_version": "device-ack.v1",
                        "command_id": command["command_id"],
                        "device_id": "biovolt-01",
                        "status": "applied",
                        "uptime_ms": 42,
                        "reason_code": None,
                        "message": None,
                        "applied_state": {
                            "mode": "manual",
                            "grow_led_pwm": 96,
                            "mixer_on": False,
                        },
                    }
                )
                time.sleep(0.02)

            for _ in range(20):
                if client.get(f"/api/experiments/{experiment_id}").json()["state"] == "running":
                    break
                time.sleep(0.01)
            assert client.get(f"/api/experiments/{experiment_id}").json()["state"] == "running"
            command_status = client.get(f"/api/commands/{commands[0]['command_id']}")
            assert command_status.status_code == 200
            assert command_status.json()["status"] == "applied"

            device.send_json(
                {
                    "schema_version": "device-ack.v1",
                    "command_id": commands[0]["command_id"],
                    "device_id": "other-device",
                    "status": "applied",
                    "uptime_ms": 43,
                    "reason_code": None,
                    "message": None,
                    "applied_state": None,
                }
            )
            assert device.receive_json() == {"error": "invalid telemetry frame"}


def test_unknown_schema_is_rejected_without_mutating_telemetry(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'unknown.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    with TestClient(app) as client:
        with client.websocket_connect(
            "/ws/device",
            headers={
                "X-BioVolt-Device-ID": "biovolt-01",
                "Authorization": f"Bearer {DEVICE_TOKEN}",
            },
        ) as device:
            device.send_text(json.dumps({"schema_version": "unknown.v1"}))
            assert device.receive_json() == {"error": "invalid telemetry frame"}


def test_required_rejection_aborts_experiment(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'lifecycle.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/experiments",
            json={
                "name": "Lifecycle run",
                "arms": [
                    {
                        "device_id": "biovolt-01",
                        "cell_id": "cell-a",
                        "mode": "passive",
                        "initial_led_pwm": 10,
                    }
                ],
            },
        ).json()
        experiment_id = created["id"]
        client.post(f"/api/experiments/{experiment_id}/ready")
        with client.websocket_connect(
            "/ws/device",
            headers={
                "X-BioVolt-Device-ID": "biovolt-01",
                "Authorization": f"Bearer {DEVICE_TOKEN}",
            },
        ) as device:
            client.post(f"/api/experiments/{experiment_id}/start")
            rejected = device.receive_json()
            device.send_json(
                {
                    "schema_version": "device-ack.v1",
                    "command_id": rejected["command_id"],
                    "device_id": "biovolt-01",
                    "status": "rejected",
                    "uptime_ms": 1,
                    "reason_code": "safety_rejected",
                    "message": "unsafe",
                    "applied_state": None,
                }
            )
            time.sleep(0.03)
            assert client.get(f"/api/experiments/{experiment_id}").json()["state"] == "aborted"


def test_safe_stop_ack_completes_running_experiment(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'stop.db'}",
            device_shared_token=DEVICE_TOKEN,
        )
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/experiments",
            json={
                "name": "Stop run",
                "arms": [
                    {
                        "device_id": "biovolt-01",
                        "cell_id": "cell-a",
                        "mode": "passive",
                        "initial_led_pwm": 10,
                    }
                ],
            },
        ).json()
        experiment_id = created["id"]
        client.post(f"/api/experiments/{experiment_id}/ready")
        with client.websocket_connect(
            "/ws/device",
            headers={
                "X-BioVolt-Device-ID": "biovolt-01",
                "Authorization": f"Bearer {DEVICE_TOKEN}",
            },
        ) as device:
            client.post(f"/api/experiments/{experiment_id}/start")
            for _ in range(2):
                command = device.receive_json()
                device.send_json(
                    {
                        "schema_version": "device-ack.v1",
                        "command_id": command["command_id"],
                        "device_id": "biovolt-01",
                        "status": "applied",
                        "uptime_ms": 1,
                        "reason_code": None,
                        "message": None,
                        "applied_state": {
                            "mode": "passive",
                            "grow_led_pwm": 10,
                            "mixer_on": False,
                        },
                    }
                )
                time.sleep(0.02)
            for _ in range(20):
                if client.get(f"/api/experiments/{experiment_id}").json()["state"] == "running":
                    break
                time.sleep(0.01)
            assert client.get(f"/api/experiments/{experiment_id}").json()["state"] == "running"

            assert (
                client.post(f"/api/experiments/{experiment_id}/stop").json()["state"] == "stopping"
            )
            stop_command = device.receive_json()
            assert stop_command["kind"] == "safe_stop"
            device.send_json(
                {
                    "schema_version": "device-ack.v1",
                    "command_id": stop_command["command_id"],
                    "device_id": "biovolt-01",
                    "status": "applied",
                    "uptime_ms": 2,
                    "reason_code": None,
                    "message": None,
                    "applied_state": {
                        "mode": "monitor",
                        "grow_led_pwm": 0,
                        "mixer_on": False,
                    },
                }
            )
            time.sleep(0.03)
            assert client.get(f"/api/experiments/{experiment_id}").json()["state"] == "completed"
