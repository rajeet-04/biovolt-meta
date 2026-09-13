import argparse
import json
from pathlib import Path

try:
    from scripts.release.validate_scientific_copy import scan
except ModuleNotFoundError:
    from validate_scientific_copy import scan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    findings = scan(args.root)
    result = {"blockers": findings, "eligible": not findings}
    print(json.dumps(result, indent=2))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
