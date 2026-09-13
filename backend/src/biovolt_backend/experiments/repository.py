from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from .models import Experiment


class ExperimentRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get(self, experiment_id: str) -> Experiment | None:
        statement = (
            select(Experiment)
            .options(selectinload(Experiment.arms))
            .where(Experiment.id == experiment_id)
        )
        async with self._session_factory() as session:
            return await session.scalar(statement)

    async def list(self) -> list[Experiment]:
        async with self._session_factory() as session:
            return list(
                await session.scalars(
                    select(Experiment)
                    .options(selectinload(Experiment.arms))
                    .order_by(Experiment.created_at.desc())
                )
            )

    async def save(self, experiment: Experiment) -> Experiment:
        async with self._session_factory() as session:
            merged = await session.merge(experiment)
            await session.commit()
            await session.refresh(merged, ["arms"])
            return merged
