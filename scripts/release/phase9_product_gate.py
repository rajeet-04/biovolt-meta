"""Gate the final product/judge audit without inventing screenshot evidence."""

import argparse
import json
from pathlib import Path


def evaluate(evidence: dict[str, object]) -> dict[str, object]:
    findings = [f"BLOCKER: {item}" for item in evidence.get("blockers", [])]
    findings.extend(f"MAJOR: {item}" for item in evidence.get("majors", []))
    journeys = evidence.get("journeys", {})
    if not isinstance(journeys, dict) or any(
        journeys.get(name) is not True for name in ("judge", "operator", "recovery")
    ):
        findings.append("MAJOR: judge, operator, and recovery journeys are incomplete")
    for name in ("responsive", "accessibility", "screenshots"):
        if evidence.get(name) is not True:
            findings.append(f"MAJOR: {name} audit evidence is incomplete")
    return {"findings": findings, "eligible": not findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.evidence.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
