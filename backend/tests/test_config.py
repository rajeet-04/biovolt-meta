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


def test_settings_load_biovol_environment(monkeypatch):
    monkeypatch.setenv("BIOVOLT_ENVIRONMENT", "staging")
    monkeypatch.setenv("BIOVOLT_DEVICE_SHARED_TOKEN", "environment-token-123")

    settings = Settings()

    assert settings.environment == "staging"
    assert settings.device_shared_token == "environment-token-123"


def test_settings_treat_blank_optional_calibration_as_unset(monkeypatch):
    monkeypatch.setenv("BIOVOLT_DEVICE_SHARED_TOKEN", "environment-token-123")
    monkeypatch.setenv("BIOVOLT_BPW34_DARK_RAW", "")
    monkeypatch.setenv("BIOVOLT_BPW34_BLANK_RAW", "   ")

    settings = Settings()

    assert settings.bpw34_dark_raw is None
    assert settings.bpw34_blank_raw is None
