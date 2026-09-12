import pytest
from pydantic import ValidationError

from biovolt_simulator.config import SimulatorSettings


def test_default_settings_values() -> None:
    settings = SimulatorSettings(
        backend_ws_url="ws://localhost:8000/ws/device",
        device_token="test-token-123",
    )

    assert settings.device_id == "biovolt-sim-01"
    assert settings.cell_id == "cell-a"
    assert settings.interval_seconds == 0.5
    assert settings.seed == 42
    assert settings.start_sequence == 1


def test_settings_load_biovoltsim_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BIOVOLT_SIM_BACKEND_WS_URL", "ws://example.test/ws")
    monkeypatch.setenv("BIOVOLT_SIM_DEVICE_ID", "sim-17")
    monkeypatch.setenv("BIOVOLT_SIM_CELL_ID", "cell-b")
    monkeypatch.setenv("BIOVOLT_SIM_DEVICE_TOKEN", "token-abc")
    monkeypatch.setenv("BIOVOLT_SIM_INTERVAL_SECONDS", "1.25")
    monkeypatch.setenv("BIOVOLT_SIM_SEED", "99")
    monkeypatch.setenv("BIOVOLT_SIM_START_SEQUENCE", "12")

    settings = SimulatorSettings()

    assert settings.backend_ws_url == "ws://example.test/ws"
    assert settings.device_id == "sim-17"
    assert settings.cell_id == "cell-b"
    assert settings.device_token == "token-abc"
    assert settings.interval_seconds == 1.25
    assert settings.seed == 99
    assert settings.start_sequence == 12


@pytest.mark.parametrize("field", ["device_token", "device_id", "cell_id"])
def test_settings_reject_blank_identifiers(field: str) -> None:
    values = {
        "backend_ws_url": "ws://localhost:8000/ws/device",
        "device_token": "test-token-123",
    }
    values[field] = "   "

    with pytest.raises(ValidationError):
        SimulatorSettings(**values)


def test_settings_reject_non_positive_interval() -> None:
    with pytest.raises(ValidationError):
        SimulatorSettings(
            backend_ws_url="ws://localhost:8000/ws/device",
            device_token="test-token-123",
            interval_seconds=0,
        )
