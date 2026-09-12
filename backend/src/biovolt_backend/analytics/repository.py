from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from biovolt_backend.persistence.models import TelemetrySample


class AnalyticsRepository:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], max_limit: int = 200_000
    ) -> None:
        self._session_factory, self._max_limit = session_factory, max_limit

    async def arm_samples(
        self,
        experiment_id: str,
        device_id: str,
        cell_id: str,
        *,
        started_at: datetime,
        ended_at: datetime | None,
        limit: int = 200_000,
    ) -> list[TelemetrySample]:
        if limit <= 0 or limit > self._max_limit:
            raise ValueError("analytics row limit is outside the configured bound")
        statement = select(TelemetrySample).where(
            TelemetrySample.device_id == device_id,
            TelemetrySample.cell_id == cell_id,
            TelemetrySample.experiment_id == experiment_id,
            TelemetrySample.received_at >= started_at,
        )
        if ended_at is not None:
            statement = statement.where(TelemetrySample.received_at <= ended_at)
        statement = statement.order_by(
            TelemetrySample.received_at.asc(), TelemetrySample.id.asc()
        ).limit(limit)
        async with self._session_factory() as session:
            return list(await session.scalars(statement))
