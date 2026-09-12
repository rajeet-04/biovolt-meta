from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import phase1_smoke  # noqa: E402
import soak_phase1  # noqa: E402


def test_smoke_acceptance_can_target_a_non_simulator_device() -> None:
    args = phase1_smoke._parser().parse_args(["--device-id", "biovolt-hw-01"])

    assert args.device_id == "biovolt-hw-01"


def test_smoke_uses_supplied_device_id_for_runtime_queries(monkeypatch) -> None:
    args = phase1_smoke._parser().parse_args(
        [
            "--base-url",
            "http://test",
            "--device-id",
            "biovolt-hw-01",
            "--cell-id",
            "cell-hw",
            "--timeout",
            "5",
            "--settle-seconds",
            "0.01",
        ]
    )
    wait_calls: list[str] = []
    fetch_calls: list[tuple[str, dict[str, str | int]]] = []

    monkeypatch.setattr(phase1_smoke, "_require_health", lambda *_args: None)

    def wait_for_device(*_args, **kwargs):
        wait_calls.append(_args[1])
        return {"connected_devices": [args.device_id]}

    def fetch_json(_base_url, path, *, timeout_seconds, **params):
        del timeout_seconds
        fetch_calls.append((path, params))
        if path == "/api/telemetry/latest":
            return {"electrical": {"voltage_mv": 1, "power_uw": 1}}
        return [{"sequence": 1}, {"sequence": 2}]

    monkeypatch.setattr(phase1_smoke, "wait_for_device", wait_for_device)
    monkeypatch.setattr(phase1_smoke, "fetch_json", fetch_json)
    monkeypatch.setattr(phase1_smoke.time, "sleep", lambda _seconds: None)

    phase1_smoke.run_smoke(args)

    assert wait_calls == ["biovolt-hw-01"]
    assert all(
        params.get("device_id") == "biovolt-hw-01" and params.get("cell_id") == "cell-hw"
        for path, params in fetch_calls
        if path in {"/api/telemetry/latest", "/api/telemetry/history"}
    )


def test_soak_checks_start_and_duration_boundary(monkeypatch) -> None:
    clock = [0.0]
    checks: list[float] = []

    monkeypatch.setattr(soak_phase1.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        soak_phase1.time, "sleep", lambda seconds: clock.__setitem__(0, clock[0] + seconds)
    )

    def check_once(_args):
        checks.append(clock[0])
        return int(clock[0]), None

    monkeypatch.setattr(soak_phase1, "_check_once", check_once)
    args = SimpleNamespace(minutes=1.0, interval_seconds=30.0, max_age_seconds=3.0)

    soak_phase1.run_soak(args)

    assert checks == [0.0, 30.0, 60.0]
