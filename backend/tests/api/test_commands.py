import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from biovolt_backend.commands.models import DeviceCommand
from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


def test_command_status_is_read_only_and_safe(tmp_path) -> None:
    app = create_app(
        Settings(environment="test", database_url=f"sqlite+aiosqlite:///{tmp_path / 'commands.db'}")
    )
    with TestClient(app) as client:
        created = client.post(
            "/api/experiments",
            json={
                "name": "Command source",
                "arms": [
                    {
                        "device_id": "biovolt-01",
                        "cell_id": "cell-a",
                        "mode": "passive",
                        "initial_led_pwm": 12,
                    }
                ],
            },
        ).json()
        client.post(f"/api/experiments/{created['id']}/ready")
        client.post(f"/api/experiments/{created['id']}/start")

        async def first_command_id() -> str:
            async with client.app.state.session_factory() as session:
                return (await session.scalar(select(DeviceCommand))).id

        command_id = asyncio.run(first_command_id())
        response = client.get(f"/api/commands/{command_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "queued"
        assert "device_shared_token" not in body
