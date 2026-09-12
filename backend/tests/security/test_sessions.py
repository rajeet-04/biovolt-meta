from datetime import UTC, datetime, timedelta

from biovolt_backend.security.sessions import OperatorSessionStore


def test_session_create_validity_expiry_and_revoke() -> None:
    store = OperatorSessionStore()
    now = datetime(2026, 8, 27, tzinfo=UTC)
    token, expires_at = store.create(now)

    assert len(token) > 20
    assert expires_at == now + timedelta(minutes=30)
    assert store.valid(token, now + timedelta(minutes=29)) is True
    assert store.valid(token, expires_at) is False
    store.revoke(token)
    assert store.valid(token, now) is False


def test_prune_removes_only_expired_sessions() -> None:
    store = OperatorSessionStore()
    now = datetime(2026, 8, 27, tzinfo=UTC)
    expired, _ = store.create(now - timedelta(minutes=31))
    current, _ = store.create(now)

    assert store.prune(now) == 1
    assert store.valid(expired, now) is False
    assert store.valid(current, now) is True
