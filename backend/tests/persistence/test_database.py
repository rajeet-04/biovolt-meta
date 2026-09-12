from sqlalchemy import text


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
