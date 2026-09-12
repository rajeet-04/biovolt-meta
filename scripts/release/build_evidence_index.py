"""Build a deterministic, secret-safe index of release evidence artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

SECRET_NAMES = (".env", "token", "password", "pin", "secret", "credential", "attestation")


def build_index(root: Path) -> dict[str, object]:
    files: list[str] = []
    excluded: list[str] = []
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if any(name in relative.lower() for name in SECRET_NAMES):
            excluded.append(relative)
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append(relative)
        entries.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
    return {"root": root.name, "files": files, "excluded": excluded, "entries": entries}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = json.dumps(build_index(args.root), indent=2) + "\n"
    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
