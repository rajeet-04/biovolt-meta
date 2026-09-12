import copy
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

import biovolt_backend.services.telemetry_service as telemetry_service_module
from biovolt_backend.contracts.loader import validate_payload as real_validate_payload
from biovolt_backend.contracts.models import DeviceTelemetryV1, ProcessedTelemetryV1
from biovolt_backend.domain.electrical import power_uw
from biovolt_backend.domain.energy import EnergyAccumulator
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

    def anchor(
        self,
        device_id: str,
        cell_id: str,
        uptime_ms: int,
        power_uw: float | None,
    ) -> float:
        return self.update(device_id, cell_id, uptime_ms, power_uw)

    def reset(self, device_id: str, cell_id: str) -> None:
        self.events.append("energy_reset")


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
    config: ProcessingConfig | None = None,
) -> tuple[TelemetryService, FakeEnergy, FakeThrottle, FakeRepository, FakeHub, FakeRegistry]:
    energy = FakeEnergy(events)
    throttle = FakeThrottle(events, allowed=allowed)
    repository = FakeRepository(events)
    hub = FakeHub(events)
    registry = FakeRegistry(events)
    service = TelemetryService(
        config=config
        or ProcessingConfig(
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


def service_with_real_energy(
    events: list[str],
) -> tuple[
    TelemetryService,
    EnergyAccumulator,
    FakeThrottle,
    FakeRepository,
    FakeHub,
    FakeRegistry,
]:
    energy = EnergyAccumulator()
    throttle = FakeThrottle(events)
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


async def test_handle_raw_uses_device_uptime_when_server_receive_is_delayed() -> None:
    events: list[str] = []
    service, _, throttle, repository, hub, registry = service_with_real_energy(events)
    first = canonical_payload()
    first["sequence"] = 100
    first["uptime_ms"] = 1000
    second = copy.deepcopy(first)
    second["sequence"] = 101
    second["uptime_ms"] = 1575
    first_received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
    second_received_at = datetime(2026, 8, 23, 12, 0, 42, tzinfo=UTC)

    await service.handle_raw(first, "biovolt-01", first_received_at)
    processed = await service.handle_raw(second, "biovolt-01", second_received_at)

    measured_power_uw = power_uw(438.2, 100_000.0)
    assert processed.timestamp == second_received_at
    assert processed.electrical.cumulative_energy_mj == pytest.approx(
        measured_power_uw * 0.575 / 1000.0
    )
    assert [payload["sequence"] for payload in hub.payloads] == [100, 101]
    assert [raw.sequence for raw, _, _ in repository.calls] == [100, 101]
    assert throttle.calls[-1][-1] == second_received_at
    assert registry.calls[-1][-1] == second_received_at


async def test_handle_raw_sequence_gap_preserves_prior_energy() -> None:
    events: list[str] = []
    service, _, _, repository, hub, _ = service_with_real_energy(events)
    first = canonical_payload()
    first["sequence"] = 100
    first["uptime_ms"] = 1000
    second = copy.deepcopy(first)
    second["sequence"] = 102
    second["uptime_ms"] = 1575
    second["electrical"]["bpv_voltage_mv"] = 876.4  # type: ignore[index]
    received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    await service.handle_raw(first, "biovolt-01", received_at)
    processed = await service.handle_raw(second, "biovolt-01", received_at)

    assert processed.sequence == 102
    assert processed.electrical.cumulative_energy_mj == 0.0
    assert [payload["sequence"] for payload in hub.payloads] == [100, 102]
    assert [raw.sequence for raw, _, _ in repository.calls] == [100, 102]


async def test_handle_raw_resumes_energy_only_after_contiguous_gap_frame() -> None:
    events: list[str] = []
    service, _, _, _, _, _ = service_with_real_energy(events)
    first = canonical_payload()
    first["sequence"] = 10
    first["uptime_ms"] = 1000
    second = copy.deepcopy(first)
    second["sequence"] = 11
    second["uptime_ms"] = 1500
    gap = copy.deepcopy(second)
    gap["sequence"] = 20
    gap["uptime_ms"] = 10000
    resumed = copy.deepcopy(gap)
    resumed["sequence"] = 21
    resumed["uptime_ms"] = 10500
    received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    await service.handle_raw(first, "biovolt-01", received_at)
    before_gap = await service.handle_raw(second, "biovolt-01", received_at)
    first_after_gap = await service.handle_raw(gap, "biovolt-01", received_at)
    resumed_processed = await service.handle_raw(resumed, "biovolt-01", received_at)

    power = power_uw(438.2, 100_000.0)
    assert first_after_gap.electrical.cumulative_energy_mj == pytest.approx(
        before_gap.electrical.cumulative_energy_mj
    )
    assert resumed_processed.electrical.cumulative_energy_mj == pytest.approx(
        before_gap.electrical.cumulative_energy_mj + power * 0.5 / 1000.0
    )


async def test_handle_raw_reboot_resets_energy_and_anchors_new_boot() -> None:
    events: list[str] = []
    service, _, _, _, _, _ = service_with_real_energy(events)
    first = canonical_payload()
    first["sequence"] = 10
    first["uptime_ms"] = 1000
    second = copy.deepcopy(first)
    second["sequence"] = 11
    second["uptime_ms"] = 1500
    reboot = copy.deepcopy(second)
    reboot["sequence"] = 0
    reboot["uptime_ms"] = 100
    received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    await service.handle_raw(first, "biovolt-01", received_at)
    await service.handle_raw(second, "biovolt-01", received_at)
    processed = await service.handle_raw(reboot, "biovolt-01", received_at)

    assert processed.electrical.cumulative_energy_mj == 0.0


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


async def test_handle_raw_rejects_naive_receive_timestamp_before_side_effects() -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)

    with pytest.raises(TelemetryRejected, match="received_at must be timezone-aware"):
        await service.handle_raw(
            canonical_payload(),
            "biovolt-01",
            datetime(2026, 8, 23, 12, 0),
        )

    assert events == []
    assert energy.calls == []
    assert throttle.calls == []
    assert repository.calls == []
    assert hub.payloads == []
    assert registry.calls == []


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
async def test_handle_raw_rejects_non_finite_numeric_values_before_side_effects(
    non_finite: float,
) -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    payload["environment"]["lux"] = non_finite  # type: ignore[index]

    with pytest.raises(TelemetryRejected, match="non-finite telemetry value"):
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


async def test_handle_raw_rejects_json_nan_before_side_effects() -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    payload["electrical"]["bpv_voltage_mv"] = json.loads("NaN")  # type: ignore[index]

    with pytest.raises(TelemetryRejected, match="non-finite telemetry value"):
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


async def test_handle_raw_rejects_overflowing_power_before_side_effects() -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    payload["electrical"]["bpv_voltage_mv"] = 1e200  # type: ignore[index]

    with pytest.raises(TelemetryRejected, match="telemetry calculation overflow"):
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


@pytest.mark.parametrize(
    ("field", "unsafe_value"),
    [("uptime_ms", 10**1000), ("sequence", 10**100)],
)
async def test_handle_raw_rejects_storage_unsafe_integers_before_side_effects(
    field: str,
    unsafe_value: int,
) -> None:
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(events)
    payload = canonical_payload()
    payload[field] = unsafe_value

    with pytest.raises(TelemetryRejected, match="storage-unsafe telemetry integer"):
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


async def test_handle_raw_rejects_cumulative_energy_overflow_without_poisoning_state() -> None:
    events: list[str] = []
    energy = EnergyAccumulator()
    throttle = FakeThrottle(events)
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
    payload = canonical_payload()
    payload["electrical"]["bpv_voltage_mv"] = 1e154  # type: ignore[index]
    first = payload.copy()
    first["uptime_ms"] = 0
    first["sequence"] = 1
    received_at = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    await service.handle_raw(first, "biovolt-01", received_at)
    repository_count = len(repository.calls)
    broadcast_count = len(hub.payloads)
    registry_count = len(registry.calls)

    overflowing = payload.copy()
    overflowing["uptime_ms"] = 2**63 - 1
    overflowing["sequence"] = 2
    with pytest.raises(TelemetryRejected, match="cumulative energy overflow"):
        await service.handle_raw(overflowing, "biovolt-01", received_at)

    assert len(repository.calls) == repository_count
    assert len(hub.payloads) == broadcast_count
    assert len(registry.calls) == registry_count

    subsequent = payload.copy()
    subsequent["uptime_ms"] = 1000
    subsequent["sequence"] = 2
    processed = await service.handle_raw(subsequent, "biovolt-01", received_at)

    assert processed.electrical.cumulative_energy_mj == pytest.approx(1e300)
    assert len(repository.calls) == repository_count + 1
    assert len(hub.payloads) == broadcast_count + 1
    assert len(registry.calls) == registry_count + 1


async def test_handle_raw_rejects_non_finite_derived_electrical_values_before_side_effects() -> (
    None
):
    events: list[str] = []
    service, energy, throttle, repository, hub, registry = service_with_fakes(
        events,
        config=ProcessingConfig(
            load_resistance_ohm=1e-306,
            bpw34_dark_raw=320,
            bpw34_blank_raw=23_840,
        ),
    )
    payload = canonical_payload()
    payload["electrical"]["bpv_voltage_mv"] = 1.0  # type: ignore[index]

    with pytest.raises(TelemetryRejected, match="non-finite derived electrical value"):
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
