"""Async SQLAlchemy engine, session, and metadata setup."""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all persistence models."""


def create_engine_and_session(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create an async engine and session factory for ``database_url``."""

    engine = create_async_engine(database_url, future=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, session_factory


async def init_database(engine: AsyncEngine) -> None:
    """Create all registered persistence tables."""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
