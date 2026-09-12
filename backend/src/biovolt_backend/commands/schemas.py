"""Pydantic command and acknowledgement contracts."""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .state import CommandStatus

CommandKind = Literal[
    "set_mode",
    "set_led_pwm",
    "set_mixer",
    "request_status",
    "safe_stop",
]
AckStatus = Literal["accepted", "applied", "rejected", "failed"]
AckReason = Literal[
    "expired",
    "invalid_payload",
    "unsupported_command",
    "phase_not_available",
    "safety_rejected",
    "cooldown_active",
    "hardware_failure",
    "internal_error",
]


class CommandCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    device_id: str = Field(min_length=1, max_length=64)
    experiment_id: str | None = Field(default=None, max_length=64)
    kind: CommandKind
    payload: dict[str, object] = Field(default_factory=dict)
    ttl_ms: int = Field(default=30_000, ge=1, le=600_000)


class CommandView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    command_id: UUID
    device_id: str
    experiment_id: str | None
    kind: CommandKind
    payload: dict[str, object]
    status: CommandStatus
    issued_at: datetime
    expires_at: datetime
    sent_at: datetime | None
    accepted_at: datetime | None
    terminal_at: datetime | None
    reason_code: str | None
    message: str | None
    applied_state: dict[str, object] | None
    send_attempts: int


class DeviceAck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["device-ack.v1"]
    command_id: UUID
    device_id: str = Field(min_length=1, max_length=64)
    status: AckStatus
    uptime_ms: int = Field(ge=0)
    reason_code: AckReason | None
    message: str | None = Field(default=None, max_length=256)
    applied_state: dict[str, object] | None


def utc_now() -> datetime:
    """Return an aware UTC timestamp for command lifecycle bookkeeping."""

    return datetime.now(UTC)
