from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


def test_create_ready_and_start_does_not_mark_running(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test", database_url=f"sqlite+aiosqlite:///{tmp_path / 'experiments.db'}"
        )
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/experiments",
            json={
                "name": "Passive run",
                "arms": [
                    {
                        "device_id": "biovolt-01",
                        "cell_id": "cell-a",
                        "mode": "passive",
                        "initial_led_pwm": 96,
                    }
                ],
            },
        ).json()
        experiment_id = created["id"]
        assert client.post(f"/api/experiments/{experiment_id}/ready").json()["state"] == "ready"
        assert client.post(f"/api/experiments/{experiment_id}/start").json()["state"] == "starting"
