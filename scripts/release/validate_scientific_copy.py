import re
from pathlib import Path

FORBIDDEN = (
    re.compile(r"permanently removed", re.IGNORECASE),
    re.compile(r"sequestered permanently", re.IGNORECASE),
    re.compile(r"\bPAR\b", re.IGNORECASE),
    re.compile(r"AI optimized", re.IGNORECASE),
)


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        # Audit judge-visible production sources only.  Dependency trees,
        # generated build output, and the release evidence itself are not
        # product copy and would create noisy false blockers (for example,
        # package documentation routinely mentions PAR).
        if any(
            part in {".git", ".venv", "node_modules", ".pio", "dist", "build"}
            for part in relative.parts
        ):
            continue
        if "docs" in relative.parts or "release" in relative.parts or "tests" in relative.parts:
            continue
        if relative.parts[:2] not in [("frontend", "src"), ("backend", "src")]:
            continue
        if path.is_file() and path.suffix in {".ts", ".tsx", ".py", ".md"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            findings.extend(f"{path}: {term.pattern}" for term in FORBIDDEN if term.search(text))
    return findings
