"""SQLAlchemy model for durable device commands."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from biovolt_backend.persistence.database import Base
from biovolt_backend.persistence.models import UTCDateTime


class DeviceCommand(Base):
    """One outbound command and its complete acknowledgement history."""

    __tablename__ = "device_commands"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    experiment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False, index=True)
    sent_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    terminal_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    reason_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    message: Mapped[str | None] = mapped_column(String(256), nullable=True)
    applied_state_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    send_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self.payload_json)

    @property
    def applied_state(self) -> dict[str, Any] | None:
        return json.loads(self.applied_state_json) if self.applied_state_json else None
