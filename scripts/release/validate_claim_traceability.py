"""Fail closed when a judge-facing headline lacks provenance."""

import argparse
import json
from pathlib import Path


def validate_claims(claims: list[dict[str, object]]) -> list[str]:
    required = ("claim", "ui_field", "api_field", "experiment", "evidence_class", "source")
    findings: list[str] = []
    for index, claim in enumerate(claims, 1):
        missing = [field for field in required if not claim.get(field)]
        if claim.get("requires_calibration") and not claim.get("calibration_revision"):
            missing.append("calibration_revision")
        if missing:
            findings.append(f"claim {index} missing trace fields: {', '.join(missing)}")
        if (
            claim.get("evidence_class") == "synthetic_demo"
            and claim.get("synthetic_label") != "synthetic_demo"
        ):
            findings.append(
                f"claim {index} synthetic evidence is not visibly labeled synthetic_demo"
            )
    return findings


def build_report(claims: list[dict[str, object]]) -> dict[str, object]:
    findings = validate_claims(claims)
    return {
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
        "claim_count": len(claims),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("claims", type=Path, help="JSON array of headline claim traces")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = build_report(json.loads(args.claims.read_text(encoding="utf-8")))
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
