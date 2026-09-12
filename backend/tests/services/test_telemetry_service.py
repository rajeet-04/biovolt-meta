import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

import biovolt_backend.services.telemetry_service as telemetry_service_module
from biovolt_backend.contracts.loader import validate_payload as real_validate_payload
from biovolt_backend.contracts.models import DeviceTelemetryV1, ProcessedTelemetryV1
from biovolt_backend.domain.processing import ProcessingConfig
from biovolt_backend.services.telemetry_service import TelemetryRejected, TelemetryService

REPO_ROOT = Path(__file__).resolve().parents[3]


def canonical_payload() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )


class FakeEnergy:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.calls: list[tuple[str, str, int, float | None]] = []

    def update(
        self,
        device_id: str,
        cell_id: str,
        uptime_ms: int,
        power_uw: float | None,
    ) -> float:
        self.events.append("energy")
        self.calls.append((device_id, cell_id, uptime_ms, power_uw))
        return 12.5


class FakeThrottle:
    def __init__(self, events: list[str], allowed: bool = True) -> None:
        self.events = events
        self.allowed = allowed
        self.calls: list[tuple[str, str, datetime]] = []

    def should_persist(self, device_id: str, cell_id: str, timestamp: datetime) -> bool:
        self.events.append("throttle")
        self.calls.append((device_id, cell_id, timestamp))
        return self.allowed


class FakeRepository:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.calls: list[tuple[DeviceTelemetryV1, ProcessedTelemetryV1, dict[str, object]]] = []

    async def save(
        self,
        raw: DeviceTelemetryV1,
        processed: ProcessedTelemetryV1,
        raw_payload: dict[str, object],
    ) -> None:
        self.events.append("repository")
        self.calls.append((raw, processed, raw_payload))


class FakeHub:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.payloads: list[dict[str, object]] = []

    async def broadcast_json(self, payload: dict[str, object]) -> None:
        self.events.append("dashboard")
        self.payloads.append(payload)


class FakeRegistry:
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.calls: list[tuple[str, datetime]] = []

    def mark_telemetry(self, device_id: str, received_at: datetime) -> None:
        self.events.append("registry")
        self.calls.append((device_id, received_at))


def service_with_fakes(
    events: list[str],
    *,
    allowed: bool = True,
) -> tuple[TelemetryService, FakeEnergy, FakeThrottle, FakeRepository, FakeHub, FakeRegistry]:
    energy = FakeEnergy(events)
    throttle = FakeThrottle(events, allowed=allowed)
    repository = FakeRepository(events)
    hub = FakeHub(events)
    registry = FakeRegistry(events)
    service = TelemetryService(
        config=ProcessingConfig(
            load_resistance_ohm=100_000.0,
            bpw34_dark_raw=320,
            bpw34_blank_raw=23_840,
        ),
        energy=energy,
        throttle=throttle,
        repository=repository,
        dashboard_hub=hub,
        device_registry=registry,
    )
    return service, energy, throttle, repository, hub, registry


async def test_handle_raw_validates_processes_persists_and_broadcasts(monkeypatch) -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
    validation_calls: list[str] = []

    def validate_payload(filename: str, candidate: dict[str, object]) -> None:
        validation_calls.append(filename)
        events.append("schema")
        real_validate_payload(filename, candidate)

    monkeypatch.setattr(telemetry_service_module, "validate_payload", validate_payload)

    processed = await service.handle_raw(payload, "biovolt-01", received_at)

    assert validation_calls == ["device-telemetry.v1.schema.json"]
    assert isinstance(processed, ProcessedTelemetryV1)
    assert processed.device_id == "biovolt-01"
    assert processed.sequence == payload["sequence"]
    assert processed.timestamp == received_at
    assert processed.electrical.cumulative_energy_mj == 12.5
    assert energy.calls[0][:3] == ("biovolt-01", "cell-a", payload["uptime_ms"])
    assert energy.calls[0][3] == pytest.approx(438.2**2 / 100_000.0)
    assert throttle.calls == [("biovolt-01", "cell-a", received_at)]
    assert registry.calls == [("biovolt-01", received_at)]
    assert len(repository.calls) == 1
    assert repository.calls[0][0].device_id == "biovolt-01"
    assert repository.calls[0][1] is processed
    assert repository.calls[0][2] is payload
    assert hub.payloads == [processed.model_dump(mode="json")]
    assert events == ["schema", "energy", "registry", "throttle", "repository", "dashboard"]


async def test_handle_raw_rejects_mismatched_authenticated_device_before_fanout() -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    payload["device_id"] = "biovolt-02"

    with pytest.raises(TelemetryRejected, match="device id mismatch"):
        await service.handle_raw(
            payload,
            "biovolt-01",
            datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
        )

    assert events == []
    assert energy.calls == []
    assert throttle.calls == []
    assert repository.calls == []
    assert hub.payloads == []
    assert registry.calls == []


async def test_handle_raw_rejects_invalid_schema_before_processing_or_fanout() -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    del payload["sequence"]

    with pytest.raises(TelemetryRejected, match="invalid telemetry payload"):
        await service.handle_raw(
            payload,
            "biovolt-01",
            datetime(2026, 8, 23, 12, 0, tzinfo=UTC),
        )

    assert events == []
    assert energy.calls == []
    assert throttle.calls == []
    assert repository.calls == []
    assert hub.payloads == []
    assert registry.calls == []
