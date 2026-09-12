from dataclasses import dataclass

from .types import AnalyticsSample


@dataclass(frozen=True)
class ArmQuality:
    sample_count: int
    valid_power_sample_count: int
    power_coverage_fraction: float
    gap_count: int
    gap_seconds: float
    telemetry_gap_fraction: float
    maximum_gap_seconds: float
    reboot_detected: bool
    biomass_extrapolation_fraction: float | None
    reasons: tuple[str, ...]


def summarize_quality(
    samples: tuple[AnalyticsSample, ...], gap_threshold_s: float = 2.5
) -> ArmQuality:
    ordered = tuple(sorted(samples, key=lambda s: s.received_at))
    gaps = [
        max(0.0, (b.received_at - a.received_at).total_seconds())
        for a, b in zip(ordered, ordered[1:], strict=False)
    ]
    excess = [g - gap_threshold_s for g in gaps if g > gap_threshold_s]
    valid = sum(s.power_uw is not None for s in ordered)
    reboot = any(b.uptime_ms < a.uptime_ms for a, b in zip(ordered, ordered[1:], strict=False))
    reasons = tuple(
        x
        for x, enabled in (
            ("device_reboot", reboot),
            ("insufficient_power_coverage", bool(ordered) and valid / len(ordered) < 0.8),
        )
        if enabled
    )
    return ArmQuality(
        len(ordered),
        valid,
        valid / len(ordered) if ordered else 0.0,
        len(excess),
        sum(excess),
        sum(excess) / max(sum(gaps), 1e-9),
        max(gaps, default=0.0),
        reboot,
        (sum(s.quality.biomass_extrapolated for s in ordered) / len(ordered) if ordered else None),
        reasons,
    )
