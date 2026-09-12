from datetime import UTC, datetime, timedelta

from biovolt_backend.persistence.throttle import PersistenceThrottle


def test_persists_at_fixed_one_hz_cadence() -> None:
    throttle = PersistenceThrottle()
    start = datetime(2026, 8, 23, tzinfo=UTC)

    decisions = [
        throttle.should_persist("d1", "c1", start + timedelta(seconds=offset))
        for offset in (0.0, 0.5, 1.0, 1.5, 2.0)
    ]

    assert decisions == [True, False, True, False, True]


def test_tracks_each_device_cell_independently() -> None:
    throttle = PersistenceThrottle(interval_seconds=1.0)
    start = datetime(2026, 8, 23, tzinfo=UTC)

    assert throttle.should_persist("d1", "c1", start) is True
    assert throttle.should_persist("d1", "c2", start) is True
    assert throttle.should_persist("d2", "c1", start) is True
    assert throttle.should_persist("d1", "c1", start + timedelta(milliseconds=500)) is False


def test_accepts_custom_interval() -> None:
    throttle = PersistenceThrottle(interval_seconds=2.0)
    start = datetime(2026, 8, 23, tzinfo=UTC)

    assert throttle.should_persist("d1", "c1", start) is True
    assert throttle.should_persist("d1", "c1", start + timedelta(seconds=1.9)) is False
    assert throttle.should_persist("d1", "c1", start + timedelta(seconds=2.0)) is True
