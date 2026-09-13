"""Monotonic command state transitions."""

from enum import StrEnum


class CommandStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    ACCEPTED = "accepted"
    APPLIED = "applied"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"


TERMINAL_STATUSES = frozenset(
    {
        CommandStatus.APPLIED,
        CommandStatus.REJECTED,
        CommandStatus.FAILED,
        CommandStatus.EXPIRED,
    }
)

_TRANSITIONS: dict[CommandStatus, frozenset[CommandStatus]] = {
    CommandStatus.QUEUED: frozenset({CommandStatus.SENT, CommandStatus.EXPIRED}),
    CommandStatus.SENT: frozenset(
        {
            CommandStatus.SENT,
            CommandStatus.ACCEPTED,
            CommandStatus.APPLIED,
            CommandStatus.REJECTED,
            CommandStatus.FAILED,
            CommandStatus.EXPIRED,
        }
    ),
    CommandStatus.ACCEPTED: frozenset(
        {
            CommandStatus.ACCEPTED,
            CommandStatus.APPLIED,
            CommandStatus.REJECTED,
            CommandStatus.FAILED,
            CommandStatus.EXPIRED,
        }
    ),
    CommandStatus.APPLIED: frozenset({CommandStatus.APPLIED}),
    CommandStatus.REJECTED: frozenset({CommandStatus.REJECTED}),
    CommandStatus.FAILED: frozenset({CommandStatus.FAILED}),
    CommandStatus.EXPIRED: frozenset({CommandStatus.EXPIRED}),
}


def can_transition(current: CommandStatus, target: CommandStatus) -> bool:
    """Return whether a command may move from ``current`` to ``target``."""

    return target in _TRANSITIONS[current]
