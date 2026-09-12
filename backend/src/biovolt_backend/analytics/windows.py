from datetime import datetime

from .types import AnalyticsSample, MatchedWindow


def select_matched_window(
    passive: tuple[AnalyticsSample, ...],
    adaptive: tuple[AnalyticsSample, ...],
    started_at: datetime,
) -> MatchedWindow:
    def elapsed(sample: AnalyticsSample) -> float:
        return (sample.received_at - started_at).total_seconds()

    p_end = max((elapsed(s) for s in passive if elapsed(s) >= 0), default=0)
    a_end = max((elapsed(s) for s in adaptive if elapsed(s) >= 0), default=0)
    duration = min(p_end, a_end)
    if duration <= 0:
        return MatchedWindow(0, (), ())
    return MatchedWindow(
        duration,
        tuple(s for s in passive if 0 <= elapsed(s) <= duration),
        tuple(s for s in adaptive if 0 <= elapsed(s) <= duration),
    )
