"""Independently recompute a matched passive/adaptive energy comparison.

The input is intentionally small and transport-independent: elapsed uptime in
milliseconds paired with electrical power in microwatts. The validator owns
its integration and quality rules so it can detect production analytics drift
without importing the production analytics package.
"""

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

Sample = tuple[int, float | None]
GAP_THRESHOLD_MS = 2_500
MINIMUM_COVERAGE = 0.8


def _interpolate(left: Sample, right: Sample, timestamp_ms: int) -> float | None:
    if left[1] is None or right[1] is None or right[0] <= left[0]:
        return None
    fraction = (timestamp_ms - left[0]) / (right[0] - left[0])
    return left[1] + (right[1] - left[1]) * fraction


def _clip_samples(samples: Sequence[Sample], start_ms: int, end_ms: int) -> list[Sample]:
    clipped: list[Sample] = []
    for index, sample in enumerate(samples):
        timestamp_ms, _ = sample
        if start_ms < timestamp_ms < end_ms:
            clipped.append(sample)
        if timestamp_ms == start_ms:
            clipped.append(sample)
        if timestamp_ms < start_ms and index + 1 < len(samples):
            right = samples[index + 1]
            if right[0] >= start_ms:
                clipped.append((start_ms, _interpolate(sample, right, start_ms)))
        if timestamp_ms < end_ms and index + 1 < len(samples):
            right = samples[index + 1]
            if right[0] >= end_ms:
                clipped.append((end_ms, _interpolate(sample, right, end_ms)))
                break
    if samples and samples[-1][0] == end_ms:
        clipped.append(samples[-1])
    return sorted(set(clipped), key=lambda sample: sample[0])


def _integrate(samples: Sequence[Sample]) -> tuple[float, float, list[str]]:
    energy_mj = 0.0
    valid_duration_ms = 0.0
    reasons: list[str] = []
    for left, right in zip(samples, samples[1:], strict=False):
        delta_ms = right[0] - left[0]
        if delta_ms <= 0:
            if "telemetry_reboot_or_nonmonotonic" not in reasons:
                reasons.append("telemetry_reboot_or_nonmonotonic")
            continue
        if delta_ms > GAP_THRESHOLD_MS:
            if "telemetry_gap" not in reasons:
                reasons.append("telemetry_gap")
            continue
        if left[1] is None or right[1] is None:
            continue
        valid_duration_ms += delta_ms
        energy_mj += (left[1] + right[1]) / 2 * delta_ms / 1_000_000
    return energy_mj, valid_duration_ms, reasons


def _has_overlapping_gap(samples: Sequence[Sample], start_ms: int, end_ms: int) -> bool:
    return any(
        right[0] > left[0]
        and right[0] - left[0] > GAP_THRESHOLD_MS
        and left[0] < end_ms
        and right[0] > start_ms
        for left, right in zip(samples, samples[1:], strict=False)
    )


def _result(
    *,
    reasons: list[str],
    evidence_class: str,
    passive_energy_mj: float | None = None,
    adaptive_energy_mj: float | None = None,
    comparison_duration_s: float | None = None,
    passive_coverage_fraction: float | None = None,
    adaptive_coverage_fraction: float | None = None,
) -> dict[str, object]:
    return {
        "eligible": not reasons,
        "passive_energy_mj": passive_energy_mj,
        "adaptive_energy_mj": adaptive_energy_mj,
        "evidence_class": evidence_class,
        "gain_pct": (
            (adaptive_energy_mj - passive_energy_mj) / passive_energy_mj * 100
            if not reasons and passive_energy_mj and passive_energy_mj > 0
            else None
        ),
        "comparison_duration_s": comparison_duration_s,
        "passive_coverage_fraction": passive_coverage_fraction,
        "adaptive_coverage_fraction": adaptive_coverage_fraction,
        "reasons": reasons,
        "reason": reasons[0] if reasons else None,
    }


def compare(
    passive: list[Sample],
    adaptive: list[Sample],
    *,
    passive_evidence: str,
    adaptive_evidence: str,
    minimum_coverage: float = MINIMUM_COVERAGE,
) -> dict[str, object]:
    reasons: list[str] = []
    evidence_class = passive_evidence if passive_evidence == adaptive_evidence else "mixed"
    if passive_evidence != "measured" or adaptive_evidence != "measured":
        reasons.append("evidence_class_not_measured")
    if not passive or not adaptive:
        reasons.append("no_common_window")
        return _result(reasons=reasons, evidence_class=evidence_class)

    if any(right[0] <= left[0] for left, right in zip(passive, passive[1:], strict=False)):
        reasons.append("telemetry_reboot_or_nonmonotonic")
    if any(right[0] <= left[0] for left, right in zip(adaptive, adaptive[1:], strict=False)):
        reasons.append("telemetry_reboot_or_nonmonotonic")

    start_ms = max(passive[0][0], adaptive[0][0])
    end_ms = min(passive[-1][0], adaptive[-1][0])
    duration_ms = end_ms - start_ms
    if duration_ms <= 0:
        reasons.append("no_common_window")
        return _result(reasons=list(dict.fromkeys(reasons)), evidence_class=evidence_class)

    if _has_overlapping_gap(passive, start_ms, end_ms) or _has_overlapping_gap(
        adaptive, start_ms, end_ms
    ):
        reasons.append("telemetry_gap")

    passive_clipped = _clip_samples(passive, start_ms, end_ms)
    adaptive_clipped = _clip_samples(adaptive, start_ms, end_ms)
    passive_energy, passive_valid_ms, passive_reasons = _integrate(passive_clipped)
    adaptive_energy, adaptive_valid_ms, adaptive_reasons = _integrate(adaptive_clipped)
    reasons.extend(passive_reasons)
    reasons.extend(adaptive_reasons)
    duration_s = duration_ms / 1000
    passive_coverage = passive_valid_ms / duration_ms
    adaptive_coverage = adaptive_valid_ms / duration_ms
    if passive_coverage < minimum_coverage:
        reasons.append("insufficient_passive_coverage")
    if adaptive_coverage < minimum_coverage:
        reasons.append("insufficient_adaptive_coverage")
    if passive_energy <= 0:
        reasons.append("nonpositive_passive_energy")
    unique_reasons = list(dict.fromkeys(reasons))
    return _result(
        reasons=unique_reasons,
        evidence_class=evidence_class,
        passive_energy_mj=passive_energy,
        adaptive_energy_mj=adaptive_energy,
        comparison_duration_s=duration_s,
        passive_coverage_fraction=passive_coverage,
        adaptive_coverage_fraction=adaptive_coverage,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "input",
        type=Path,
        help="JSON object with passive/adaptive [uptime_ms, power_uw] arrays and evidence classes",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = compare(
        [tuple(sample) for sample in payload["passive"]],
        [tuple(sample) for sample in payload["adaptive"]],
        passive_evidence=payload["passive_evidence"],
        adaptive_evidence=payload["adaptive_evidence"],
    )
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
