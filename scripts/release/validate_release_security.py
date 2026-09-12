"""Scan release material for obvious secret exposure and public writes."""

import argparse
import json
import re
from pathlib import Path

SECRET_ASSIGNMENT = re.compile(
    r"(?im)[\"']?[A-Z0-9_]*(?:TOKEN|PASSWORD|PIN|WIFI_PASSWORD|SECRET)[\"']?\s*[:=]\s*"
    r"[\"']?(?![<${\[]|example\b|changeme\b|replace\b)[^\s,;}\"']{4,}"
)


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file() or any(
            part in {".git", ".venv", "node_modules", ".pio"} for part in path.parts
        ):
            continue
        if path.suffix not in {".md", ".json", ".yml", ".yaml", ".env"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if SECRET_ASSIGNMENT.search(text) and "example" not in path.name:
            findings.append(f"secret-like value in release material: {path}")
        if "POST /api" in text or "POST /ws" in text:
            findings.append(f"public mutation example requires review: {path}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    findings = scan(args.root)
    report = {"status": "PASS" if not findings else "FAIL", "findings": findings}
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
