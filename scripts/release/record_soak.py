"""Append one JSON soak observation from stdin or a supplied JSON object."""

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument(
        "--sample", required=True, help="JSON object containing one soak observation"
    )
    args = parser.parse_args()
    with args.output.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(json.loads(args.sample), sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
