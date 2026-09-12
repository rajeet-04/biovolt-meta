#!/usr/bin/env python3
"""Create a consistent SQLite backup without exposing database contents."""
import argparse
import sqlite3
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.source) as source, sqlite3.connect(args.destination) as destination:
        source.backup(destination)
    print(f"Backup written to {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
