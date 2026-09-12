from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


def test_system_status_reports_connected_device_ids_and_telemetry_age(tmp_path) -> None:
    app = create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'status.db'}",
        )
    )

    with TestClient(app) as client:
        registry = client.app.state.device_registry
        registry.connect("biovolt-01", object())
        registry.connect("biovolt-02", object())
        received_at = datetime.now(UTC) - timedelta(milliseconds=250)
        registry.mark_telemetry("biovolt-01", received_at)

        response = client.get("/api/system/status")

    assert response.status_code == 200
    body = response.json()
    assert body["backend"] == "ok"
    assert body["database"] == "ok"
    assert body["connected_devices"] == ["biovolt-01", "biovolt-02"]
    assert body["device_count"] == 2
    assert set(body["devices"]) == {"biovolt-01", "biovolt-02"}
    assert body["devices"]["biovolt-01"]["latest_telemetry_at"].endswith("Z")
    assert 0 <= body["devices"]["biovolt-01"]["latest_telemetry_age_ms"] < 2_000
    assert body["devices"]["biovolt-02"] == {
        "latest_telemetry_at": None,
        "latest_telemetry_age_ms": None,
    }
