from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from biovolt_backend.persistence.database import (
    create_engine_and_session,
    init_database,
)


@pytest_asyncio.fixture
async def db_engine(tmp_path) -> AsyncIterator[AsyncEngine]:
    """Provide an initialized, isolated SQLite engine per test."""

    engine, _ = create_engine_and_session(
        f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
    )
    await init_database(engine)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Provide a session factory paired with the isolated test engine."""

    return async_sessionmaker(db_engine, expire_on_commit=False)
