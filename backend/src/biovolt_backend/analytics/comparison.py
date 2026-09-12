from dataclasses import dataclass

from .metrics import electrical_metrics
from .quality import summarize_quality
from .types import MatchedWindow


@dataclass(frozen=True)
class EnergyComparison:
    eligible: bool
    passive_energy_mj: float | None
    adaptive_energy_mj: float | None
    gain_pct: float | None
    common_duration_s: float | None
    reasons: tuple[str, ...]


def compare_energy(
    window: MatchedWindow, *, evidence_class: str = "measured", minimum_coverage: float = 0.8
) -> EnergyComparison:
    reasons: list[str] = []
    if evidence_class == "synthetic_demo":
        reasons.append("synthetic_demo")
    if window.duration_s <= 0:
        reasons.append("no_common_duration")
    p_quality, a_quality = (
        summarize_quality(window.passive_samples),
        summarize_quality(window.adaptive_samples),
    )
    if p_quality.power_coverage_fraction < minimum_coverage:
        reasons.append("insufficient_passive_coverage")
    if a_quality.power_coverage_fraction < minimum_coverage:
        reasons.append("insufficient_adaptive_coverage")
    passive = electrical_metrics(window.passive_samples, window.duration_s).energy_mj
    adaptive = electrical_metrics(window.adaptive_samples, window.duration_s).energy_mj
    if passive is None or adaptive is None:
        reasons.append("missing_energy")
    if passive is not None and passive <= 0:
        reasons.append("nonpositive_passive_energy")
    eligible = not reasons
    return EnergyComparison(
        eligible,
        passive,
        adaptive,
        (adaptive - passive) / passive * 100 if eligible and passive else None,
        window.duration_s or None,
        tuple(reasons),
    )
