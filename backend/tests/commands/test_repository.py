from datetime import UTC, datetime, timedelta

import pytest

from biovolt_backend.commands.models import DeviceCommand
from biovolt_backend.commands.repository import CommandRepository
from biovolt_backend.commands.state import CommandStatus


def _command(command_id: str, *, device_id: str = "biovolt-01", issued_at=None) -> DeviceCommand:
    issued_at = issued_at or datetime.now(UTC)
    return DeviceCommand(
        id=command_id,
        device_id=device_id,
        experiment_id=None,
        kind="request_status",
        payload_json="{}",
        status=CommandStatus.QUEUED,
        issued_at=issued_at,
        expires_at=issued_at + timedelta(seconds=30),
        send_attempts=0,
    )


@pytest.mark.asyncio
async def test_save_get_and_pending_commands_are_ordered(db_session_factory) -> None:
    repository = CommandRepository(db_session_factory)
    now = datetime.now(UTC)
    await repository.save(_command("00000000-0000-0000-0000-000000000001", issued_at=now))
    await repository.save(
        _command(
            "00000000-0000-0000-0000-000000000002",
            issued_at=now + timedelta(seconds=1),
        )
    )

    found = await repository.get("00000000-0000-0000-0000-000000000001")
    pending = await repository.pending_for_device("biovolt-01", now)

    assert found is not None
    assert [item.id for item in pending] == [
        "00000000-0000-0000-0000-000000000001",
        "00000000-0000-0000-0000-000000000002",
    ]


@pytest.mark.asyncio
async def test_expire_due_only_marks_unfinished_commands(db_session_factory) -> None:
    repository = CommandRepository(db_session_factory)
    now = datetime.now(UTC)
    expired = _command("00000000-0000-0000-0000-000000000003", issued_at=now - timedelta(minutes=1))
    applied = _command("00000000-0000-0000-0000-000000000004", issued_at=now - timedelta(minutes=1))
    applied.status = CommandStatus.APPLIED
    await repository.save(expired)
    await repository.save(applied)

    assert await repository.expire_due(now) == 1
    assert (await repository.get(expired.id)).status == CommandStatus.EXPIRED
    assert (await repository.get(applied.id)).status == CommandStatus.APPLIED
