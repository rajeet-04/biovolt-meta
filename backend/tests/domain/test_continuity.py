from biovolt_backend.domain.continuity import TelemetryContinuityTracker


def test_first_frame_is_an_anchor() -> None:
    result = TelemetryContinuityTracker().observe("d1", "c1", 100, 5000)

    assert not result.contiguous
    assert not result.restarted


def test_next_sequence_with_increasing_uptime_is_contiguous() -> None:
    tracker = TelemetryContinuityTracker()
    tracker.observe("d1", "c1", 100, 5000)

    assert tracker.observe("d1", "c1", 101, 5500).contiguous


def test_gap_duplicate_and_older_sequence_are_discontinuities() -> None:
    tracker = TelemetryContinuityTracker()
    tracker.observe("d1", "c1", 100, 5000)

    assert not tracker.observe("d1", "c1", 103, 6500).contiguous
    assert not tracker.observe("d1", "c1", 103, 7000).contiguous
    assert not tracker.observe("d1", "c1", 99, 7500).contiguous


def test_decreasing_uptime_is_a_reboot() -> None:
    tracker = TelemetryContinuityTracker()
    tracker.observe("d1", "c1", 100, 5000)

    result = tracker.observe("d1", "c1", 0, 100)

    assert not result.contiguous
    assert result.restarted


def test_reset_forgets_one_source() -> None:
    tracker = TelemetryContinuityTracker()
    tracker.observe("d1", "c1", 100, 5000)
    tracker.reset("d1", "c1")

    assert not tracker.observe("d1", "c1", 100, 5000).contiguous

