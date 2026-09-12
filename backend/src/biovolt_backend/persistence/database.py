"""Async SQLAlchemy engine, session, and metadata setup."""

from sqlalchemy import inspect, text
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

    # Register ORM tables before creating metadata. The local import avoids a
    # module cycle because models inherit from Base defined in this module.
    from biovolt_backend.persistence import models  # noqa: F401

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        if connection.dialect.name == "sqlite":
            await connection.run_sync(_migrate_sqlite_telemetry_resistance)


def _migrate_sqlite_telemetry_resistance(sync_connection) -> None:
    """Add resistance provenance to Phase 1.3 SQLite databases created earlier."""

    columns = {
        column["name"] for column in inspect(sync_connection).get_columns("telemetry_samples")
    }
    if "load_resistance_ohm" not in columns:
        # Legacy rows cannot recover their original resistance; preserve them
        # with the documented default while new writes provide exact values.
        sync_connection.execute(
            text(
                "ALTER TABLE telemetry_samples "
                "ADD COLUMN load_resistance_ohm FLOAT NOT NULL DEFAULT 100000.0"
            )
        )
