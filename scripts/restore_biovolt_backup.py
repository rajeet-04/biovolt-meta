#!/usr/bin/env python3
"""Restore a SQLite backup into a separate destination database."""
import argparse
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.destination.exists():
        raise SystemExit(f"refusing to overwrite existing destination: {args.destination}")
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.backup) as source, sqlite3.connect(args.destination) as destination:
        source.backup(destination)
    print(f"Restore written to {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
