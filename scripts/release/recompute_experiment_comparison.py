"""Independently recompute a matched passive/adaptive energy comparison."""


def _energy(samples: list[tuple[int, float]]) -> float | None:
    if len(samples) < 2 or any(
        right[0] <= left[0] for left, right in zip(samples, samples[1:], strict=False)
    ):
        return None
    return sum(
        (left[1] + right[1]) / 2 * (right[0] - left[0]) / 1_000_000
        for left, right in zip(samples, samples[1:], strict=False)
    )


def compare(
    passive: list[tuple[int, float]],
    adaptive: list[tuple[int, float]],
    *,
    passive_evidence: str,
    adaptive_evidence: str,
) -> dict[str, object]:
    if passive_evidence != "measured" or adaptive_evidence != "measured":
        return {
            "eligible": False,
            "gain_pct": None,
            "reason": "both experiments require measured evidence",
        }
    passive_energy = _energy(passive)
    adaptive_energy = _energy(adaptive)
    if passive_energy is None or adaptive_energy is None:
        return {"eligible": False, "gain_pct": None, "reason": "telemetry continuity is invalid"}
    if passive_energy <= 0:
        return {
            "eligible": False,
            "gain_pct": None,
            "reason": "passive denominator must be positive",
        }
    return {
        "eligible": True,
        "passive_energy_mj": passive_energy,
        "adaptive_energy_mj": adaptive_energy,
        "gain_pct": (adaptive_energy - passive_energy) / passive_energy * 100,
        "reason": None,
    }
