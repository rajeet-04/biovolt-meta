"""Compare independent and production analytics with frozen tolerances."""

import argparse
import json
from pathlib import Path


def _number_finding(
    field: str,
    independent: dict[str, object],
    production: dict[str, object],
    *,
    absolute_floor: float,
    relative_fraction: float = 0.0,
) -> str | None:
    expected, actual = independent.get(field), production.get(field)
    if expected is None or actual is None:
        return f"{field} is missing from independent or production analytics"
    tolerance = max(absolute_floor, abs(float(expected)) * relative_fraction)
    if abs(float(expected) - float(actual)) > tolerance:
        return f"{field} exceeds its release tolerance ({tolerance:g})"
    return None


def validate(independent: dict[str, object], production: dict[str, object]) -> list[str]:
    findings: list[str] = []
    if independent.get("eligible") != production.get("eligible"):
        findings.append("eligibility disagrees between independent and production analytics")
    if independent.get("evidence_class") != production.get("evidence_class"):
        findings.append("evidence_class disagrees between independent and production analytics")
    if independent.get("comparison_duration_s") != production.get("comparison_duration_s"):
        findings.append(
            "comparison_duration_s disagrees between independent and production analytics"
        )
    if independent.get("eligible"):
        for field, floor, relative in (
            ("passive_energy_mj", 0.001, 0.001),
            ("adaptive_energy_mj", 0.001, 0.001),
            ("gain_pct", 0.05, 0.0),
        ):
            finding = _number_finding(
                field,
                independent,
                production,
                absolute_floor=floor,
                relative_fraction=relative,
            )
            if finding:
                findings.append(finding)
        for field in ("passive_coverage_fraction", "adaptive_coverage_fraction"):
            if field not in independent and field not in production:
                continue
            finding = _number_finding(field, independent, production, absolute_floor=0.001)
            if finding:
                findings.append(finding)
    else:
        independent_reasons = independent.get("reasons", [independent.get("reason")])
        production_reasons = production.get("reasons", [production.get("reason")])
        if independent_reasons != production_reasons:
            findings.append("ineligible comparison reasons disagree")
    return findings


def build_report(
    independent: dict[str, object], production: dict[str, object]
) -> dict[str, object]:
    findings = validate(independent, production)
    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "independent": independent,
        "production": production,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("independent", type=Path, help="independent recomputation JSON")
    parser.add_argument("production", type=Path, help="captured production API JSON")
    parser.add_argument("--output", type=Path, help="write the report to this path")
    args = parser.parse_args()
    report = build_report(
        json.loads(args.independent.read_text(encoding="utf-8")),
        json.loads(args.production.read_text(encoding="utf-8")),
    )
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
