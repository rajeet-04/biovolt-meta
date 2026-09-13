"""Persistence queries for outbound device commands."""

import json
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .models import DeviceCommand


class CommandRepository:
    """Save and query commands through a caller-provided session factory."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, command: DeviceCommand) -> DeviceCommand:
        async with self._session_factory() as session:
            merged = await session.merge(command)
            await session.commit()
            await session.refresh(merged)
            return merged

    async def get(self, command_id: str) -> DeviceCommand | None:
        async with self._session_factory() as session:
            return await session.get(DeviceCommand, command_id)

    async def pending_for_device(self, device_id: str, now: datetime) -> Sequence[DeviceCommand]:
        now = now.astimezone(UTC)
        statement = (
            select(DeviceCommand)
            .where(
                DeviceCommand.device_id == device_id,
                DeviceCommand.expires_at > now,
                DeviceCommand.status.not_in(("applied", "rejected", "failed", "expired")),
            )
            .order_by(DeviceCommand.issued_at.asc())
        )
        async with self._session_factory() as session:
            result = await session.scalars(statement)
            return list(result)

    async def expire_due_commands(self, now: datetime) -> list[DeviceCommand]:
        statement = select(DeviceCommand).where(
            DeviceCommand.expires_at <= now,
            DeviceCommand.status.in_(("queued", "sent", "accepted")),
        )
        async with self._session_factory() as session:
            result = await session.scalars(statement)
            commands = list(result)
            for command in commands:
                command.status = "expired"
                command.reason_code = "expired"
                command.terminal_at = now
            await session.commit()
            return commands

    async def expire_due(self, now: datetime) -> int:
        """Mark all due non-terminal commands expired and return their count."""

        return len(await self.expire_due_commands(now))


def encode_payload(payload: dict[str, object]) -> str:
    """Encode contract payloads deterministically for durable storage."""

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
