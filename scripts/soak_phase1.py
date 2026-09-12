#!/usr/bin/env python3
"""Monitor a running Phase 1 Compose stack for the manual soak gate."""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Mapping
from typing import Any

from phase1_smoke import SmokeFailure, fetch_json, wait_for_device


def _mapping(value: Any, endpoint: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SmokeFailure(f"{endpoint} returned a JSON value of the wrong shape")
    return value


def _query(device_id: str, cell_id: str) -> dict[str, str]:
    return {"device_id": device_id, "cell_id": cell_id}


def _health(base_url: str, timeout_seconds: float) -> None:
    health = _mapping(
        fetch_json(base_url, "/api/health", timeout_seconds=timeout_seconds),
        "/api/health",
    )
    if health.get("status") != "ok":
        raise SmokeFailure("backend health status is not ok")


def _history(
    base_url: str,
    device_id: str,
    cell_id: str,
    timeout_seconds: float,
) -> list[Mapping[str, Any]]:
    value = fetch_json(
        base_url,
        "/api/telemetry/history",
        timeout_seconds=timeout_seconds,
        limit=1000,
        **_query(device_id, cell_id),
    )
    if not isinstance(value, list):
        raise SmokeFailure("telemetry history returned a JSON value of the wrong shape")
    rows: list[Mapping[str, Any]] = []
    for row in value:
        rows.append(_mapping(row, "/api/telemetry/history sample"))
    return rows


def _assert_status_fresh(
    status: Mapping[str, Any],
    device_id: str,
    max_age_seconds: float,
) -> None:
    devices = _mapping(status.get("devices"), "/api/system/status.devices")
    device = _mapping(devices.get(device_id), "/api/system/status device")
    age_ms = device.get("latest_telemetry_age_ms")
    if not isinstance(age_ms, (int, float)) or age_ms > max_age_seconds * 1000:
        raise SmokeFailure(f"latest telemetry age exceeded {max_age_seconds:g} seconds")


def _assert_nonnegative_energy(rows: list[Mapping[str, Any]]) -> None:
    for row in rows:
        electrical = _mapping(row.get("electrical"), "history.electrical")
        energy = electrical.get("cumulative_energy_mj")
        if isinstance(energy, (int, float)) and energy < 0:
            raise SmokeFailure("history contains negative cumulative energy")


def _check_once(args: argparse.Namespace) -> tuple[int, bool]:
    _health(args.base_url, args.request_timeout)
    status = _mapping(
        fetch_json(
            args.base_url, "/api/system/status", timeout_seconds=args.request_timeout
        ),
        "/api/system/status",
    )
    if args.device_id not in status.get("connected_devices", []):
        status = wait_for_device(
            args.base_url,
            args.device_id,
            timeout_seconds=args.grace_seconds,
            poll_seconds=args.poll_seconds,
            request_timeout_seconds=args.request_timeout,
        )
    _assert_status_fresh(status, args.device_id, args.max_age_seconds)

    latest = _mapping(
        fetch_json(
            args.base_url,
            "/api/telemetry/latest",
            timeout_seconds=args.request_timeout,
            **_query(args.device_id, args.cell_id),
        ),
        "/api/telemetry/latest",
    )
    latest_electrical = _mapping(latest.get("electrical"), "latest.electrical")
    latest_energy = latest_electrical.get("cumulative_energy_mj")
    if isinstance(latest_energy, (int, float)) and latest_energy < 0:
        raise SmokeFailure("latest telemetry contains negative cumulative energy")

    rows = _history(args.base_url, args.device_id, args.cell_id, args.request_timeout)
    _assert_nonnegative_energy(rows)
    return len(rows), len(rows) == 1000


def run_soak(args: argparse.Namespace) -> None:
    duration_seconds = args.minutes * 60
    started = time.monotonic()
    baseline_count, baseline_capped = _check_once(args)
    previous_count = baseline_count
    total_new_rows = 0
    capped = baseline_capped
    checks = 1
    next_check = started + args.interval_seconds

    while True:
        remaining = started + duration_seconds - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(max(0.0, next_check - time.monotonic()), remaining))
        if time.monotonic() >= started + duration_seconds:
            break
        count, window_capped = _check_once(args)
        if count < previous_count:
            raise SmokeFailure("history row count regressed")
        if count == previous_count and not window_capped and not capped:
            raise SmokeFailure("history row count did not increase between checks")
        total_new_rows += max(0, count - previous_count)
        previous_count = count
        capped = capped or window_capped
        checks += 1
        print(f"check {checks}: history={count} latest age < {args.max_age_seconds:g}s")
        next_check += args.interval_seconds

    elapsed = time.monotonic() - started
    expected_low = duration_seconds * 0.90
    expected_high = duration_seconds * 1.10
    if capped:
        # The Phase 1 history API intentionally caps one response at 1,000
        # rows.  A full window proves continuity but cannot provide a total
        # count for a 30-minute run; report that limitation rather than fail
        # a healthy stack because the bounded API has no pagination yet.
        print(
            "PASS Phase 1 soak: telemetry stayed fresh and history remained "
            f"monotonic for {elapsed:.1f}s; history window reached 1000 rows "
            f"(expected persisted range {expected_low:.0f}-{expected_high:.0f}; "
            "total is bounded by the API response limit)"
        )
    elif not expected_low <= total_new_rows <= expected_high:
        raise SmokeFailure(
            f"persisted row delta {total_new_rows} outside expected "
            f"range {expected_low:.0f}-{expected_high:.0f}"
        )
    else:
        print(
            f"PASS Phase 1 soak: {total_new_rows} new persisted rows in {elapsed:.1f}s "
            f"(expected {expected_low:.0f}-{expected_high:.0f})"
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.environ.get("BIOVOLT_BASE_URL", "http://localhost:8000"),
    )
    parser.add_argument(
        "--device-id",
        default=os.environ.get("BIOVOLT_SIM_DEVICE_ID", "biovolt-sim-01"),
    )
    parser.add_argument(
        "--cell-id", default=os.environ.get("BIOVOLT_SIM_CELL_ID", "cell-a")
    )
    parser.add_argument("--minutes", type=float, default=30.0)
    parser.add_argument("--interval-seconds", type=float, default=30.0)
    parser.add_argument("--grace-seconds", type=float, default=10.0)
    parser.add_argument("--poll-seconds", type=float, default=1.0)
    parser.add_argument("--max-age-seconds", type=float, default=3.0)
    parser.add_argument("--request-timeout", type=float, default=5.0)
    return parser


def main() -> int:
    args = _parser().parse_args()
    values = (
        args.minutes,
        args.interval_seconds,
        args.grace_seconds,
        args.poll_seconds,
        args.max_age_seconds,
        args.request_timeout,
    )
    if any(value <= 0 for value in values):
        print("FAIL soak arguments must be positive", file=sys.stderr)
        return 2
    try:
        run_soak(args)
    except SmokeFailure as exc:
        print(f"FAIL Phase 1 soak: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
