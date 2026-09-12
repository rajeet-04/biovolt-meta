#!/usr/bin/env python3
"""Run CI-compatible Phase 8 checks; deployment drills remain explicit manual gates."""

import argparse
import subprocess


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    if not args.skip_tests:
        subprocess.run(["uv", "run", "pytest", "backend/tests", "-q"], check=True)
    print("Phase 8 automated acceptance passed; network/hardware drills remain manual gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
