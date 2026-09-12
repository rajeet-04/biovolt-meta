from datetime import UTC, datetime

from sqlalchemy import inspect, select

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
