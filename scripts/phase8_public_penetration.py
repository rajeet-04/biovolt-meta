#!/usr/bin/env python3
"""Small fail-closed smoke matrix for a running public listener."""

import argparse
import urllib.error
import urllib.request


def request(url: str, method: str) -> int:
    try:
        request = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8081")
    args = parser.parse_args()
    checks = [
        ("/api/health", "GET", {200}),
        ("/api/experiments", "POST", {403, 404, 405}),
        ("/api/operator/login", "POST", {403, 404, 405}),
        ("/ws/device", "GET", {403, 404}),
    ]
    failures = []
    for path, method, expected in checks:
        status = request(args.base_url + path, method)
        if status not in expected:
            failures.append((method, path, status, expected))
    if failures:
        raise SystemExit(f"public penetration failures: {failures}")
    print("Public read-only penetration smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
