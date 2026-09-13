#!/usr/bin/env python3
"""Poll the public local health endpoints after a production cold start."""
import argparse
import time
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    for _ in iter(int, 1):
        try:
            for path in ("/healthz", "/api/health"):
                with urllib.request.urlopen(args.base_url + path, timeout=3) as response:
                    if response.status != 200:
                        raise OSError(f"{path}: HTTP {response.status}")
            print("BioVolt production cold start is healthy")
            return 0
        except OSError:
            if time.monotonic() >= deadline:
                raise SystemExit("BioVolt production cold start timed out")
            time.sleep(2)


if __name__ == "__main__":
    raise SystemExit(main())
