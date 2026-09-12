#!/usr/bin/env python3
"""Independently validate exported BioVolt experiment analytics (stdlib only)."""

import argparse
import csv
import json
from pathlib import Path


def number(value: str | None) -> float | None:
    if value in (None, "", "null", "None"):
        return None
    return float(value)


def validate(
    path: Path, passive_id: str, adaptive_id: str, gap_threshold: float = 2.5
) -> dict[str, object]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        raise ValueError("CSV contains no rows")
    by_arm: dict[str, list[dict[str, object]]] = {passive_id: [], adaptive_id: []}
    for raw in rows:
        arm_id = raw.get("arm_id", "")
        if arm_id in by_arm:
            by_arm[arm_id].append(
                {
                    **raw,
                    "elapsed_s": number(raw.get("elapsed_s")),
                    "power_uw": number(raw.get("power_uw")),
                    "cumulative_energy_mj": number(raw.get("cumulative_energy_mj")),
                    "uptime_ms": int(raw.get("uptime_ms", "0")),
                }
            )
    reasons: list[str] = []
    for arm_id in (passive_id, adaptive_id):
        if not by_arm[arm_id]:
            reasons.append(f"missing_{arm_id}_arm")
        else:
            expected = "passive" if arm_id == passive_id else "adaptive"
            if by_arm[arm_id][0].get("arm_mode") != expected:
                reasons.append(f"{arm_id}_mode_mismatch")
    evidence = str(rows[0].get("evidence_class", "measured"))
    if evidence == "synthetic_demo":
        reasons.append("synthetic_demo")
    ends = {
        arm_id: max((float(r["elapsed_s"] or 0) for r in values), default=0.0)
        for arm_id, values in by_arm.items()
    }
    common_duration = min(ends.values()) if ends else 0.0
    metrics: dict[str, dict[str, object]] = {}
    for arm_id, values in by_arm.items():
        values = sorted(
            (r for r in values if float(r["elapsed_s"] or 0) <= common_duration),
            key=lambda r: float(r["elapsed_s"] or 0),
        )
        powers = [r["power_uw"] for r in values if r["power_uw"] is not None]
        energies = [r["cumulative_energy_mj"] for r in values]
        energy = (
            energies[-1] - energies[0]
            if len(energies) >= 2
            and all(v is not None for v in energies)
            and all(b >= a for a, b in zip(energies, energies[1:], strict=False))
            else None
        )
        gaps = [
            float(b["elapsed_s"] or 0) - float(a["elapsed_s"] or 0)
            for a, b in zip(values, values[1:], strict=False)
        ]
        reboot = any(
            int(b["uptime_ms"]) < int(a["uptime_ms"])
            for a, b in zip(values, values[1:], strict=False)
        )
        if reboot:
            reasons.append(f"{arm_id}_device_reboot")
        if energy is None:
            reasons.append(f"missing_{arm_id}_energy")
        if values and len(powers) / len(values) < 0.8:
            reasons.append(f"insufficient_{arm_id}_coverage")
        if any(g > gap_threshold for g in gaps):
            reasons.append(f"{arm_id}_telemetry_gap")
        metrics[arm_id] = {
            "sample_count": len(values),
            "valid_power_count": len(powers),
            "coverage_fraction": len(powers) / len(values) if values else 0.0,
            "energy_mj": energy,
            "maximum_gap_s": max(gaps, default=0.0),
            "reboot_detected": reboot,
        }
    passive_energy, adaptive_energy = (
        metrics[passive_id]["energy_mj"],
        metrics[adaptive_id]["energy_mj"],
    )
    gain = (
        (adaptive_energy - passive_energy) / passive_energy * 100
        if isinstance(passive_energy, (int, float))
        and isinstance(adaptive_energy, (int, float))
        and passive_energy > 0
        else None
    )
    if passive_energy is not None and passive_energy <= 0:
        reasons.append("nonpositive_passive_energy")
    return {
        "evidence_class": evidence,
        "common_duration_s": common_duration or None,
        "passive": metrics[passive_id],
        "adaptive": metrics[adaptive_id],
        "gain_pct": gain,
        "eligible": not reasons,
        "reasons": sorted(set(reasons)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--passive-arm", required=True)
    parser.add_argument("--adaptive-arm", required=True)
    parser.add_argument("--gap-threshold", type=float, default=2.5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(args.csv, args.passive_arm, args.adaptive_arm, args.gap_threshold)
    print(
        json.dumps(result, sort_keys=True)
        if args.json
        else json.dumps(result, indent=2, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
