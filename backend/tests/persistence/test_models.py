from datetime import UTC, datetime

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError

from biovolt_backend.persistence.database import create_engine_and_session, init_database
from biovolt_backend.persistence.models import TelemetrySample


async def test_telemetry_samples_table_is_created(tmp_path):
    engine, _ = create_engine_and_session(f"sqlite+aiosqlite:///{tmp_path / 'models.db'}")
    await init_database(engine)

    async with engine.connect() as connection:
        table_names = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names()
        )

    assert "telemetry_samples" in table_names
    await engine.dispose()


async def test_telemetry_sample_preserves_nullable_sensor_values(tmp_path):
    engine, session_factory = create_engine_and_session(
        f"sqlite+aiosqlite:///{tmp_path / 'nulls.db'}"
    )
    await init_database(engine)
    sample = TelemetrySample(
        received_at=datetime.now(UTC),
        device_id="device-1",
        cell_id="cell-1",
        sequence=1,
        uptime_ms=100,
        temperature_c=None,
        grow_led_pwm=0,
        mixer_on=False,
        control_mode="monitor",
        raw_payload_json={"temperature_c": None},
    )
    async with session_factory() as session:
        session.add(sample)
        await session.commit()
        loaded = await session.scalar(
            select(TelemetrySample).where(TelemetrySample.id == sample.id)
        )

    assert loaded is not None
    assert loaded.temperature_c is None
    assert loaded.raw_payload_json == {"temperature_c": None}
    await engine.dispose()


async def test_telemetry_sample_preserves_aware_received_at(tmp_path):
    engine, session_factory = create_engine_and_session(
        f"sqlite+aiosqlite:///{tmp_path / 'timestamps.db'}"
    )
    await init_database(engine)
    received_at = datetime(2026, 8, 23, 12, 34, 56, tzinfo=UTC)
    sample = TelemetrySample(
        received_at=received_at,
        device_id="device-1",
        cell_id="cell-1",
        sequence=1,
        uptime_ms=100,
        grow_led_pwm=0,
        mixer_on=False,
        control_mode="monitor",
        raw_payload_json={},
    )
    async with session_factory() as session:
        session.add(sample)
        await session.commit()
        sample_id = sample.id

    async with session_factory() as session:
        loaded = await session.scalar(
            select(TelemetrySample).where(TelemetrySample.id == sample_id)
        )

    assert loaded is not None
    assert loaded.received_at.tzinfo is not None
    assert loaded.received_at.utcoffset() == received_at.utcoffset()
    await engine.dispose()


@pytest.mark.parametrize(
    "required_column", ["grow_led_pwm", "mixer_on", "control_mode", "raw_payload_json"]
)
async def test_telemetry_sample_rejects_null_required_columns(tmp_path, required_column):
    engine, session_factory = create_engine_and_session(
        f"sqlite+aiosqlite:///{tmp_path / f'{required_column}.db'}"
    )
    await init_database(engine)
    values = {
        "received_at": datetime.now(UTC),
        "device_id": "device-1",
        "cell_id": "cell-1",
        "sequence": 1,
        "uptime_ms": 100,
        "grow_led_pwm": 0,
        "mixer_on": False,
        "control_mode": "monitor",
        "raw_payload_json": {},
    }
    values[required_column] = None

    async with session_factory() as session:
        session.add(TelemetrySample(**values))
        with pytest.raises(IntegrityError):
            await session.commit()

    await engine.dispose()
