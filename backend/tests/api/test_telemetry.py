from datetime import UTC, datetime
from types import SimpleNamespace

from fastapi.testclient import TestClient

from biovolt_backend.config import Settings
from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.main import create_app


def _sample(sequence: int = 1245) -> SimpleNamespace:
    return SimpleNamespace(
        id=sequence,
        received_at=datetime(2026, 8, 23, 12, 0, sequence % 60, tzinfo=UTC),
        device_id="biovolt-01",
        cell_id="cell-a",
        sequence=sequence,
        uptime_ms=sequence * 500,
        bpv_voltage_mv=438.2,
        current_ua=4.382,
        power_uw=1.9201924,
        load_resistance_ohm=100_000.0,
        cumulative_energy_mj=1.25,
        od680=0.42,
        temperature_c=24.5,
        lux=120.0,
        grow_led_pwm=130,
        mixer_on=True,
        control_mode="adaptive",
        raw_payload_json={"sequence": sequence},
        bpv_adc_raw=1000,
        bpw34_raw=900,
        bpw34_voltage_mv=120.0,
    )


class FakeTelemetryRepository:
    def __init__(self, latest_result=None, history_result=None) -> None:
        self.latest_result = latest_result
        self.history_result = history_result or []
        self.latest_calls: list[tuple[str, str]] = []
        self.history_calls: list[tuple[str, str, int]] = []

    async def health_check(self) -> bool:
        return True

    async def latest(self, device_id: str, cell_id: str):
        self.latest_calls.append((device_id, cell_id))
        return self.latest_result

    async def history(self, device_id: str, cell_id: str, limit: int):
        self.history_calls.append((device_id, cell_id, limit))
        return self.history_result


def _app(tmp_path, load_resistance_ohm: float = 100_000.0):
    return create_app(
        Settings(
            environment="test",
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'telemetry.db'}",
            load_resistance_ohm=load_resistance_ohm,
        )
    )


def test_latest_returns_404_when_repository_has_no_data(tmp_path) -> None:
    app = _app(tmp_path)

    with TestClient(app) as client:
        repository = FakeTelemetryRepository()
        client.app.state.telemetry_repository = repository

        response = client.get(
            "/api/telemetry/latest",
            params={"device_id": "biovolt-01", "cell_id": "cell-a"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "telemetry not found"}
    assert repository.latest_calls == [("biovolt-01", "cell-a")]


def test_latest_preserves_sample_time_load_resistance_provenance(tmp_path) -> None:
    app = _app(tmp_path, load_resistance_ohm=200_000.0)

    with TestClient(app) as client:
        repository = FakeTelemetryRepository(latest_result=_sample())
        client.app.state.telemetry_repository = repository

        response = client.get(
            "/api/telemetry/latest",
            params={"device_id": "biovolt-01", "cell_id": "cell-a"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["electrical"]["load_resistance_ohm"] == 100_000.0
    validate_payload("processed-telemetry.v1.schema.json", body)


def test_latest_returns_processed_row_through_repository(tmp_path) -> None:
    app = _app(tmp_path)

    with TestClient(app) as client:
        repository = FakeTelemetryRepository(latest_result=_sample())
        client.app.state.telemetry_repository = repository

        response = client.get(
            "/api/telemetry/latest",
            params={"device_id": "biovolt-01", "cell_id": "cell-a"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["device_id"] == "biovolt-01"
    assert body["cell_id"] == "cell-a"
    assert body["sequence"] == 1245
    assert body["timestamp"] == "2026-08-23T12:00:45Z"
    assert body["electrical"] == {
        "voltage_mv": 438.2,
        "current_ua": 4.382,
        "power_uw": 1.9201924,
        "load_resistance_ohm": 100_000.0,
        "cumulative_energy_mj": 1.25,
    }
    assert body["biological"]["od680"] == 0.42
    validate_payload("processed-telemetry.v1.schema.json", body)
    assert repository.latest_calls == [("biovolt-01", "cell-a")]


def test_history_uses_bounded_default_limit_and_returns_rows(tmp_path) -> None:
    app = _app(tmp_path)

    with TestClient(app) as client:
        repository = FakeTelemetryRepository(history_result=[_sample(1), _sample(2)])
        client.app.state.telemetry_repository = repository

        response = client.get(
            "/api/telemetry/history",
            params={"device_id": "biovolt-01", "cell_id": "cell-a"},
        )

    assert response.status_code == 200
    rows = response.json()
    assert [row["sequence"] for row in rows] == [1, 2]
    for row in rows:
        validate_payload("processed-telemetry.v1.schema.json", row)
    assert repository.history_calls == [("biovolt-01", "cell-a", 100)]


def test_history_rejects_limit_above_configured_maximum(tmp_path) -> None:
    app = _app(tmp_path)

    with TestClient(app) as client:
        response = client.get(
            "/api/telemetry/history",
            params={
                "device_id": "biovolt-01",
                "cell_id": "cell-a",
                "limit": 1_001,
            },
        )

    assert response.status_code == 422
