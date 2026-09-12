from sqlalchemy import inspect, text


async def test_database_connection_is_usable(tmp_path):
    from biovolt_backend.persistence.database import (
        create_engine_and_session,
        init_database,
    )

    url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    engine, session_factory = create_engine_and_session(url)
    await init_database(engine)
    async with session_factory() as session:
        value = await session.scalar(text("SELECT 1"))
    assert value == 1
    await engine.dispose()


async def test_database_initialization_registers_telemetry_tables(tmp_path):
    from biovolt_backend.persistence.database import create_engine_and_session, init_database

    engine, _ = create_engine_and_session(f"sqlite+aiosqlite:///{tmp_path / 'clean.db'}")
    await init_database(engine)

    async with engine.connect() as connection:
        table_names = await connection.run_sync(
            lambda sync_connection: inspect(sync_connection).get_table_names()
        )

    assert "telemetry_samples" in table_names
    await engine.dispose()
