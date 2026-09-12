from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

import soak_phase1  # noqa: E402


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
