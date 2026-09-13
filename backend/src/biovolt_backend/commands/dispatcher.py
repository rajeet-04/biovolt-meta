"""Expiry-aware delivery of persisted commands to connected devices."""

from datetime import UTC, datetime

from biovolt_backend.contracts.loader import validate_payload
from biovolt_backend.websocket.device_registry import DeviceRegistry

from .repository import CommandRepository
from .schemas import CommandView
from .service import CommandService
from .state import TERMINAL_STATUSES


class CommandDispatcher:
    """Deliver commands only after durable persistence and while still valid."""

    def __init__(
        self,
        repository: CommandRepository,
        service: CommandService,
        registry: DeviceRegistry,
    ) -> None:
        self._repository = repository
        self._service = service
        self._registry = registry

    async def dispatch(self, command_id: str) -> CommandView:
        command = await self._repository.get(command_id)
        if command is None:
            return await self._service.get(command_id)
        now = datetime.now(UTC)
        if command.status in TERMINAL_STATUSES:
            return self._service._view(command)
        if now >= command.expires_at:
            return await self._service.mark_sent(command_id)
        envelope = {
            "schema_version": "device-command.v1",
            "command_id": command.id,
            "device_id": command.device_id,
            "experiment_id": command.experiment_id,
            "issued_at": command.issued_at.isoformat(),
            "expires_at": command.expires_at.isoformat(),
            "ttl_ms": max(1, int((command.expires_at - command.issued_at).total_seconds() * 1000)),
            "kind": command.kind,
            "payload": command.payload,
        }
        validate_payload("device-command.v1.schema.json", envelope)
        if not await self._registry.send_json(command.device_id, envelope):
            return self._service._view(command)
        return await self._service.mark_sent(command_id)

    async def dispatch_pending_for_device(self, device_id: str) -> int:
        now = datetime.now(UTC)
        await self._service.expire_due(now)
        pending = await self._repository.pending_for_device(device_id, now)
        delivered = 0
        for command in pending:
            before = command.send_attempts
            result = await self.dispatch(command.id)
            if result.send_attempts > before:
                delivered += 1
        return delivered
