import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "validate_phase7_analytics.py"
FIXTURES = ROOT / "backend" / "tests" / "fixtures" / "analytics"


def run(name: str) -> dict:
    output = subprocess.check_output(
        [
            sys.executable,
            str(SCRIPT),
            "--csv",
            str(FIXTURES / name),
            "--passive-arm",
            "passive",
            "--adaptive-arm",
            "adaptive",
            "--json",
        ],
        text=True,
    )
    return json.loads(output)


def test_positive_gain_is_exact():
    result = run("positive_gain.csv")
    assert result["gain_pct"] == pytest.approx(20.0)
    assert result["eligible"] is True


def test_negative_gain_is_retained():
    assert run("negative_gain.csv")["gain_pct"] == pytest.approx(-20.0)


def test_unequal_duration_uses_shorter_window():
    assert run("unequal_duration.csv")["common_duration_s"] == 10


def test_gap_and_reboot_are_caveats():
    assert "insufficient_passive_coverage" in run("gapped.csv")["reasons"]
    assert "passive_device_reboot" in run("reboot.csv")["reasons"]


def test_synthetic_is_not_eligible():
    result = run("synthetic.csv")
    assert result["evidence_class"] == "synthetic_demo"
    assert "synthetic_demo" in result["reasons"]
