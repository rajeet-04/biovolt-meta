from datetime import UTC, datetime, timedelta

import pytest

from biovolt_backend.commands.dispatcher import CommandDispatcher
from biovolt_backend.commands.repository import CommandRepository
from biovolt_backend.commands.schemas import CommandCreate
from biovolt_backend.commands.service import CommandService
from biovolt_backend.websocket.device_registry import DeviceRegistry


class Socket:
    def __init__(self) -> None:
        self.payloads: list[dict[str, object]] = []

    async def send_json(self, payload: dict[str, object]) -> None:
        self.payloads.append(payload)


@pytest.mark.asyncio
async def test_dispatch_persists_before_send_and_marks_sent(db_session_factory) -> None:
    repository = CommandRepository(db_session_factory)
    service = CommandService(repository)
    registry = DeviceRegistry()
    socket = Socket()
    registry.connect("biovolt-01", socket)
    dispatcher = CommandDispatcher(repository, service, registry)
    command = await service.create(
        CommandCreate(device_id="biovolt-01", kind="set_led_pwm", payload={"pwm": 32})
    )

    result = await dispatcher.dispatch(str(command.command_id))

    assert result.status == "sent"
    assert result.send_attempts == 1
    assert socket.payloads[0]["schema_version"] == "device-command.v1"


@pytest.mark.asyncio
async def test_disconnected_dispatch_leaves_command_nonterminal(db_session_factory) -> None:
    repository = CommandRepository(db_session_factory)
    service = CommandService(repository)
    dispatcher = CommandDispatcher(repository, service, DeviceRegistry())
    command = await service.create(CommandCreate(device_id="missing", kind="safe_stop"))

    result = await dispatcher.dispatch(str(command.command_id))

    assert result.status == "queued"
    assert result.send_attempts == 0


@pytest.mark.asyncio
async def test_expired_command_is_not_sent_on_reconnect(db_session_factory) -> None:
    repository = CommandRepository(db_session_factory)
    service = CommandService(repository)
    registry = DeviceRegistry()
    socket = Socket()
    registry.connect("biovolt-01", socket)
    dispatcher = CommandDispatcher(repository, service, registry)
    command = await service.create(CommandCreate(device_id="biovolt-01", kind="safe_stop"))
    stored = await repository.get(str(command.command_id))
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await repository.save(stored)

    result = await dispatcher.dispatch_pending_for_device("biovolt-01")

    assert result == 0
    assert socket.payloads == []
    assert (await repository.get(str(command.command_id))).status == "expired"
