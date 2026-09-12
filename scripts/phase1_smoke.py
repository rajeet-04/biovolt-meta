#!/usr/bin/env python3
"""Run a short acceptance check against a running Phase 1 stack.

The script deliberately uses only the Python standard library so it can be
run from the repository root without installing another client package.  It
does not start or stop Docker services and never accepts a token argument;
authentication is handled by the simulator already connected to the backend.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SmokeFailure(RuntimeError):
    """Raised when an acceptance assertion cannot be satisfied."""


def _url(base_url: str, path: str, **params: str | int) -> str:
    base = base_url.rstrip("/")
    query = urlencode(params)
    return f"{base}{path}?{query}" if query else f"{base}{path}"


def fetch_json(
    base_url: str,
    path: str,
    *,
    timeout_seconds: float,
    **params: str | int,
) -> Any:
    """Fetch one JSON endpoint and hide response bodies from error output."""

    request = Request(
        _url(base_url, path, **params),
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except HTTPError as exc:
        raise SmokeFailure(f"GET {path} returned HTTP {exc.code}") from exc
    except URLError as exc:
        raise SmokeFailure(f"GET {path} failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise SmokeFailure(f"GET {path} timed out") from exc

    try:
        return json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SmokeFailure(f"GET {path} returned invalid JSON") from exc


def _require_mapping(value: Any, endpoint: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SmokeFailure(f"{endpoint} returned a JSON value of the wrong shape")
    return value


def _require_health(base_url: str, timeout_seconds: float) -> None:
    health = _require_mapping(
        fetch_json(base_url, "/api/health", timeout_seconds=timeout_seconds),
        "/api/health",
    )
    if health.get("status") != "ok":
        raise SmokeFailure("backend health status is not ok")


def _device_present(status: Mapping[str, Any], device_id: str) -> bool:
    connected = status.get("connected_devices")
    return isinstance(connected, list) and device_id in connected


def wait_for_device(
    base_url: str,
    device_id: str,
    *,
    timeout_seconds: float,
    poll_seconds: float,
    request_timeout_seconds: float,
) -> Mapping[str, Any]:
    """Wait for the expected device to register, returning its latest status."""

    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SmokeFailure(f"device {device_id!r} did not connect before timeout")
        status = _require_mapping(
            fetch_json(
                base_url,
                "/api/system/status",
                timeout_seconds=min(request_timeout_seconds, remaining),
            ),
            "/api/system/status",
        )
        if _device_present(status, device_id):
            return status
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise SmokeFailure(f"device {device_id!r} did not connect before timeout")
        time.sleep(min(poll_seconds, remaining))


def _telemetry_query(device_id: str, cell_id: str) -> dict[str, str]:
    return {"device_id": device_id, "cell_id": cell_id}


def run_smoke(args: argparse.Namespace) -> None:
    started = time.monotonic()
    deadline = started + min(args.timeout, 29.0)

    def remaining() -> float:
        value = deadline - time.monotonic()
        if value <= 0:
            raise SmokeFailure("smoke checks exceeded the overall time limit")
        return value

    _require_health(args.base_url, min(args.request_timeout, remaining()))
    wait_for_device(
        args.base_url,
        args.device_id,
        timeout_seconds=remaining(),
        poll_seconds=args.poll_seconds,
        request_timeout_seconds=min(args.request_timeout, remaining()),
    )

    latest: Mapping[str, Any] | None = None
    while time.monotonic() < deadline:
        try:
            latest = _require_mapping(
                fetch_json(
                    args.base_url,
                    "/api/telemetry/latest",
                    timeout_seconds=min(args.request_timeout, remaining()),
                    **_telemetry_query(args.device_id, args.cell_id),
                ),
                "/api/telemetry/latest",
            )
            break
        except SmokeFailure as exc:
            if "HTTP 404" not in str(exc):
                raise
            time.sleep(min(args.poll_seconds, remaining()))
    if latest is None:
        raise SmokeFailure("latest telemetry did not become available before timeout")

    electrical = _require_mapping(latest.get("electrical"), "latest.electrical")
    if electrical.get("voltage_mv") is not None and electrical.get("power_uw") is None:
        raise SmokeFailure("latest telemetry has voltage but no derived power_uw")

    if remaining() < args.settle_seconds:
        raise SmokeFailure("not enough time remained for the history settling check")
    time.sleep(args.settle_seconds)
    history_value = fetch_json(
        args.base_url,
        "/api/telemetry/history",
        timeout_seconds=min(args.request_timeout, remaining()),
        limit=1000,
        **_telemetry_query(args.device_id, args.cell_id),
    )
    if not isinstance(history_value, list) or len(history_value) < 2:
        raise SmokeFailure("history did not contain multiple persisted samples")

    elapsed = time.monotonic() - started
    if elapsed >= 30:
        raise SmokeFailure(f"smoke checks exceeded 30 seconds ({elapsed:.1f}s)")
    print(
        f"PASS Phase 1 smoke: {len(history_value)} persisted samples in {elapsed:.1f}s"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BIOVOLT_BASE_URL", "http://localhost:8000"),
        help="backend HTTP origin (default: BIOVOLT_BASE_URL or localhost:8000)",
    )
    parser.add_argument(
        "--device-id",
        default=os.environ.get("BIOVOLT_SIM_DEVICE_ID", "biovolt-sim-01"),
    )
    parser.add_argument(
        "--cell-id",
        default=os.environ.get("BIOVOLT_SIM_CELL_ID", "cell-a"),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="overall smoke limit in seconds (capped at 29)",
    )
    parser.add_argument("--poll-seconds", type=float, default=0.5)
    parser.add_argument("--settle-seconds", type=float, default=3.0)
    parser.add_argument("--request-timeout", type=float, default=5.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if any(
        value <= 0
        for value in (
            args.timeout,
            args.poll_seconds,
            args.settle_seconds,
            args.request_timeout,
        )
    ):
        print("FAIL smoke arguments must be positive", file=sys.stderr)
        return 2
    try:
        run_smoke(args)
    except SmokeFailure as exc:
        print(f"FAIL Phase 1 smoke: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
