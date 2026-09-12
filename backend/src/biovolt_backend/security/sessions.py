"""In-memory digest-keyed operator sessions."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta


class OperatorSessionStore:
    """Store only SHA-256 token digests with a hard 30-minute lifetime."""

    LIFETIME = timedelta(minutes=30)

    def __init__(self) -> None:
        self._sessions: dict[bytes, datetime] = {}

    @staticmethod
    def _digest(token: str) -> bytes:
        return hashlib.sha256(token.encode("utf-8")).digest()

    def create(self, now: datetime) -> tuple[str, datetime]:
        now = self._utc(now)
        token = secrets.token_urlsafe(32)
        expires_at = now + self.LIFETIME
        self._sessions[self._digest(token)] = expires_at
        return token, expires_at

    def valid(self, token: str, now: datetime) -> bool:
        if not token:
            return False
        expires_at = self._sessions.get(self._digest(token))
        return expires_at is not None and self._utc(now) < expires_at

    def expires_at(self, token: str) -> datetime | None:
        """Return expiry for a currently stored token without exposing its digest."""

        return self._sessions.get(self._digest(token))

    def revoke(self, token: str) -> None:
        self._sessions.pop(self._digest(token), None)

    def prune(self, now: datetime) -> int:
        now = self._utc(now)
        expired = [digest for digest, expires_at in self._sessions.items() if expires_at <= now]
        for digest in expired:
            del self._sessions[digest]
        return len(expired)

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("session time must be timezone-aware")
        return value.astimezone(UTC)
