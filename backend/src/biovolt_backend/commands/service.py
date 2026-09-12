"""Command lifecycle service with acknowledgement correlation."""

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException
from jsonschema.exceptions import ValidationError as JsonSchemaValidationError

from biovolt_backend.contracts.loader import validate_payload

from .models import DeviceCommand
from .repository import CommandRepository, encode_payload
from .schemas import CommandCreate, CommandView, DeviceAck, utc_now
from .state import TERMINAL_STATUSES, CommandStatus, can_transition

AckHandler = Callable[[CommandView, DeviceAck], Awaitable[None]]


class CommandService:
    """Own command creation, monotonic transitions, and ack application."""

    def __init__(
        self, repository: CommandRepository, ack_handler: AckHandler | None = None
    ) -> None:
        self._repository = repository
        self._ack_handler = ack_handler

    def set_ack_handler(self, handler: AckHandler) -> None:
        self._ack_handler = handler

    @staticmethod
    def _view(command: DeviceCommand) -> CommandView:
        return CommandView(
            command_id=command.id,
            device_id=command.device_id,
            experiment_id=command.experiment_id,
            kind=command.kind,
            payload=command.payload,
            status=command.status,
            issued_at=command.issued_at,
            expires_at=command.expires_at,
            sent_at=command.sent_at,
            accepted_at=command.accepted_at,
            terminal_at=command.terminal_at,
            reason_code=command.reason_code,
            message=command.message,
            applied_state=command.applied_state,
            send_attempts=command.send_attempts,
        )

    async def create(self, request: CommandCreate) -> CommandView:
        issued_at = utc_now()
        command_id = str(uuid4())
        expires_at = issued_at + timedelta(milliseconds=request.ttl_ms)
        envelope = {
            "schema_version": "device-command.v1",
            "command_id": command_id,
            "device_id": request.device_id,
            "experiment_id": request.experiment_id,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "ttl_ms": request.ttl_ms,
            "kind": request.kind,
            "payload": request.payload,
        }
        try:
            validate_payload("device-command.v1.schema.json", envelope)
        except JsonSchemaValidationError as exc:
            raise HTTPException(422, "invalid command payload") from exc
        command = DeviceCommand(
            id=command_id,
            device_id=request.device_id,
            experiment_id=request.experiment_id,
            kind=request.kind,
            payload_json=encode_payload(request.payload),
            status=CommandStatus.QUEUED,
            issued_at=issued_at,
            expires_at=expires_at,
            send_attempts=0,
        )
        return self._view(await self._repository.save(command))

    async def get(self, command_id: str) -> CommandView:
        command = await self._repository.get(command_id)
        if command is None:
            raise HTTPException(404, "command not found")
        return self._view(command)

    async def mark_sent(self, command_id: str) -> CommandView:
        command = await self._require(command_id)
        now = utc_now()
        if command.status in TERMINAL_STATUSES:
            return self._view(command)
        if now >= command.expires_at:
            return await self._expire(command, now)
        if not can_transition(CommandStatus(command.status), CommandStatus.SENT):
            raise ValueError(f"cannot mark {command.status} command sent")
        command.status = CommandStatus.SENT
        command.sent_at = command.sent_at or now
        command.send_attempts += 1
        return self._view(await self._repository.save(command))

    async def apply_ack(self, ack: DeviceAck) -> CommandView:
        command = await self._require(str(ack.command_id))
        if command.device_id != ack.device_id:
            raise ValueError("ack device id does not match command")
        current = CommandStatus(command.status)
        target = CommandStatus(ack.status)
        if current in TERMINAL_STATUSES:
            # Terminal acknowledgements are idempotent. A repeated ack cannot
            # overwrite the original applied state or reason.
            return self._view(command)
        if not can_transition(current, target):
            raise ValueError(f"cannot apply {ack.status} acknowledgement to {command.status}")
        now = utc_now()
        command.status = target
        command.reason_code = ack.reason_code
        command.message = ack.message
        if ack.applied_state is not None:
            command.applied_state_json = encode_payload(ack.applied_state)
        if target == CommandStatus.ACCEPTED:
            command.accepted_at = command.accepted_at or now
        if target in TERMINAL_STATUSES:
            command.terminal_at = command.terminal_at or now
        saved = await self._repository.save(command)
        view = self._view(saved)
        if self._ack_handler is not None:
            await self._ack_handler(view, ack)
        return view

    async def expire_due(self, now: datetime) -> int:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        expired = await self._repository.expire_due_commands(now.astimezone(UTC))
        if self._ack_handler is not None:
            for command in expired:
                view = self._view(command)
                await self._ack_handler(
                    view,
                    DeviceAck(
                        schema_version="device-ack.v1",
                        command_id=UUID(command.id),
                        device_id=command.device_id,
                        status="failed",
                        uptime_ms=0,
                        reason_code="expired",
                        message="command expired before application",
                        applied_state=None,
                    ),
                )
        return len(expired)

    async def _require(self, command_id: str) -> DeviceCommand:
        command = await self._repository.get(command_id)
        if command is None:
            raise HTTPException(404, "command not found")
        return command

    async def _expire(self, command: DeviceCommand, now: datetime) -> CommandView:
        command.status = CommandStatus.EXPIRED
        command.reason_code = "expired"
        command.terminal_at = now
        return self._view(await self._repository.save(command))
