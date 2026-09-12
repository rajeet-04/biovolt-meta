"""Scan release material for obvious secret exposure and public writes."""

import re
from pathlib import Path

SECRET = re.compile(r"(?:BIOVOLT_)?(?:TOKEN|PASSWORD|PIN|WIFI_PASSWORD|SECRET)", re.IGNORECASE)


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
        if SECRET.search(text) and "example" not in path.name:
            findings.append(f"secret-like name in release material: {path}")
        if "POST /api" in text or "POST /ws" in text:
            findings.append(f"public mutation example requires review: {path}")
    return findings
