from biovolt_backend.config import Settings


def test_settings_accept_test_overrides():
    settings = Settings(
        environment="test",
        database_url="sqlite+aiosqlite:///:memory:",
        device_shared_token="test-token",
        load_resistance_ohm=100_000.0,
    )
    assert settings.environment == "test"
    assert settings.load_resistance_ohm == 100_000.0
