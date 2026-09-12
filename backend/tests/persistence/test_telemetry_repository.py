import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from biovolt_backend.contracts.models import DeviceTelemetryV1
from biovolt_backend.domain.processing import ProcessingConfig, build_processed_telemetry
from biovolt_backend.persistence.telemetry_repository import TelemetryRepository

REPO_ROOT = Path(__file__).resolve().parents[3]


def canonical_raw() -> DeviceTelemetryV1:
    payload = json.loads(
        (REPO_ROOT / "shared/examples/device-telemetry.example.json").read_text(encoding="utf-8")
    )
    return DeviceTelemetryV1.model_validate(payload)


def processed_for(raw: DeviceTelemetryV1, timestamp: datetime):
    return build_processed_telemetry(
        raw,
        timestamp=timestamp,
        config=ProcessingConfig(
            load_resistance_ohm=100_000.0,
            bpw34_dark_raw=320,
            bpw34_blank_raw=23_840,
        ),
        cumulative_energy_mj=1.25,
    )


async def test_save_and_latest_return_processed_query_fields(db_session_factory) -> None:
    raw = canonical_raw()
    processed = processed_for(raw, datetime(2026, 8, 23, 12, 0, tzinfo=UTC))
    repository = TelemetryRepository(db_session_factory)

    saved = await repository.save(raw, processed, raw.model_dump(mode="json"))
    latest = await repository.latest(raw.device_id, raw.cell_id)

    assert saved.id is not None
    assert latest is not None
    assert latest.sequence == raw.sequence
    assert latest.power_uw == processed.electrical.power_uw
    assert latest.cumulative_energy_mj == processed.electrical.cumulative_energy_mj


async def test_history_is_bounded_to_newest_rows_and_returned_oldest_to_newest(
    db_session_factory,
) -> None:
    repository = TelemetryRepository(db_session_factory)
    start = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)

    for sequence in range(1, 11):
        raw = canonical_raw().model_copy(update={"sequence": sequence, "uptime_ms": sequence * 500})
        processed = processed_for(raw, start + timedelta(seconds=sequence))
        await repository.save(raw, processed, raw.model_dump(mode="json"))

    history = await repository.history("biovolt-01", "cell-a", limit=3)

    assert [sample.sequence for sample in history] == [8, 9, 10]


async def test_save_preserves_raw_payload_nested_optical_and_health_state(
    db_session_factory,
) -> None:
    raw = canonical_raw()
    raw_payload = raw.model_dump(mode="json")
    processed = processed_for(raw, datetime(2026, 8, 23, 12, 0, tzinfo=UTC))
    repository = TelemetryRepository(db_session_factory)

    await repository.save(raw, processed, raw_payload)
    latest = await repository.latest(raw.device_id, raw.cell_id)

    assert latest is not None
    round_tripped = json.loads(json.dumps(latest.raw_payload_json))
    assert round_tripped["sequence"] == raw_payload["sequence"]
    assert round_tripped["optical"] == raw_payload["optical"]
    assert round_tripped["health"] == raw_payload["health"]
