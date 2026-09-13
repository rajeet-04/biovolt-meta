from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


def test_capabilities_are_read_only_for_public_mode(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'cap.db'}",
            device_shared_token="abcdefgh",
        )
    )
    with TestClient(app) as client:
        response = client.get(
            "/api/capabilities", headers={"X-BioVolt-Access-Mode": "public_read_only"}
        )
    assert response.status_code == 200
    assert response.json() == {
        "access_mode": "public_read_only",
        "can_control": False,
        "can_manage_experiments": False,
        "can_manage_calibration": False,
        "can_view_live": True,
        "can_export": True,
    }


def test_invalid_access_mode_is_rejected(tmp_path):
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'cap.db'}",
            device_shared_token="abcdefgh",
        )
    )
    with TestClient(app) as client:
        response = client.get("/api/capabilities", headers={"X-BioVolt-Access-Mode": "admin"})
    assert response.status_code == 400
