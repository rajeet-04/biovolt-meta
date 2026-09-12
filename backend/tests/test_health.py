import pytest
from httpx import ASGITransport, AsyncClient

from biovolt_backend.config import Settings
from biovolt_backend.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint():
    app = create_app(
        Settings(
            environment="test",
            database_url="sqlite+aiosqlite:///:memory:",
            device_shared_token="test-token-123",
        )
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
