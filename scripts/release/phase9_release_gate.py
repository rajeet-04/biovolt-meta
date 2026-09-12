"""Fail-closed final release-candidate gate."""

import argparse
import json
from pathlib import Path

REQUIRED = ("scientific", "resilience", "product", "security", "analytics", "traceability", "ci")


def evaluate_release(evidence: dict[str, object]) -> dict[str, object]:
    failed = [name for name in REQUIRED if evidence.get(name) is not True]
    blockers = int(evidence.get("blockers", 0))
    majors = int(evidence.get("majors", 0))
    if blockers:
        failed.append("blockers")
    if majors:
        failed.append("majors")
    return {"status": "PASS" if not failed else "FAIL", "failed_gates": failed}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = evaluate_release(json.loads(args.evidence.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
