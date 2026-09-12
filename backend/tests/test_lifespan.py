from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


def test_lifespan_exposes_runtime_services(tmp_path) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'lifespan.db'}",
        device_shared_token="test-token-123",
    )
    app = create_app(settings)

    with TestClient(app):
        for service_name in (
            "settings",
            "engine",
            "session_factory",
            "telemetry_repository",
            "device_registry",
            "dashboard_hub",
            "telemetry_service",
        ):
            assert hasattr(app.state, service_name), service_name
