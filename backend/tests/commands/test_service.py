from datetime import UTC, datetime, timedelta

import pytest

from biovolt_backend.commands.repository import CommandRepository
from biovolt_backend.commands.schemas import CommandCreate, DeviceAck
from biovolt_backend.commands.service import CommandService


@pytest.mark.asyncio
async def test_create_mark_sent_and_apply_ack(db_session_factory) -> None:
    service = CommandService(CommandRepository(db_session_factory))
    created = await service.create(
        CommandCreate(
            device_id="biovolt-01",
            kind="set_led_pwm",
            payload={"pwm": 96},
            ttl_ms=10_000,
        )
    )
    sent = await service.mark_sent(str(created.command_id))
    applied = await service.apply_ack(
        DeviceAck(
            schema_version="device-ack.v1",
            command_id=created.command_id,
            device_id="biovolt-01",
            status="applied",
            uptime_ms=22,
            reason_code=None,
            message=None,
            applied_state={"mode": "manual", "grow_led_pwm": 96, "mixer_on": False},
        )
    )

    assert sent.status == "sent"
    assert sent.send_attempts == 1
    assert applied.status == "applied"
    assert applied.applied_state["grow_led_pwm"] == 96


@pytest.mark.asyncio
async def test_mismatched_ack_device_is_rejected(db_session_factory) -> None:
    service = CommandService(CommandRepository(db_session_factory))
    created = await service.create(CommandCreate(device_id="biovolt-01", kind="safe_stop"))
    await service.mark_sent(str(created.command_id))

    with pytest.raises(ValueError, match="device id"):
        await service.apply_ack(
            DeviceAck(
                schema_version="device-ack.v1",
                command_id=created.command_id,
                device_id="other-device",
                status="applied",
                uptime_ms=1,
                reason_code=None,
                message=None,
                applied_state=None,
            )
        )


@pytest.mark.asyncio
async def test_terminal_ack_is_idempotent(db_session_factory) -> None:
    service = CommandService(CommandRepository(db_session_factory))
    created = await service.create(CommandCreate(device_id="biovolt-01", kind="safe_stop"))
    await service.mark_sent(str(created.command_id))
    ack = DeviceAck(
        schema_version="device-ack.v1",
        command_id=created.command_id,
        device_id="biovolt-01",
        status="applied",
        uptime_ms=1,
        reason_code=None,
        message=None,
        applied_state={"mode": "monitor", "grow_led_pwm": 0, "mixer_on": False},
    )
    first = await service.apply_ack(ack)
    second = await service.apply_ack(ack.model_copy(update={"applied_state": None}))

    assert first.status == second.status == "applied"
    assert second.applied_state == first.applied_state


@pytest.mark.asyncio
async def test_expired_command_is_not_marked_sent(db_session_factory) -> None:
    service = CommandService(CommandRepository(db_session_factory))
    created = await service.create(
        CommandCreate(device_id="biovolt-01", kind="safe_stop", ttl_ms=1)
    )
    stored = await service._repository.get(str(created.command_id))
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await service._repository.save(stored)
    result = await service.mark_sent(str(created.command_id))
    assert result.status == "expired"
