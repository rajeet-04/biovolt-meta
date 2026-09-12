import sqlite3
from pathlib import Path

from scripts.release.analyze_soak import analyze
from scripts.release.phase9_resilience_gate import evaluate
from scripts.release.validate_actuator_events import validate_events
from scripts.release.validate_cold_start import validate_runs
from scripts.release.validate_failures import validate_matrix
from scripts.release.validate_post_soak_data import validate_database
from scripts.release.validate_sensor_faults import validate_faults


def test_cold_start_requires_three_fast_safe_runs() -> None:
    runs = [
        {
            "mandatory_healthy_s": 42,
            "telemetry_recovery_s": 12,
            "boot_actuator_safe": True,
            "fake_live": False,
        }
        for _ in range(3)
    ]
    assert validate_runs(runs) == []
    assert validate_runs(runs[:2])


def test_failure_matrix_requires_truthful_recovery() -> None:
    record = {
        "scenario": "backend_restart",
        "recovery_s": 20,
        "state": "stale",
        "safe": True,
        "replayed": False,
    }
    assert validate_matrix([record]) == []
    assert validate_matrix([{**record, "state": "live"}])


def test_sensor_faults_require_null_unavailable_and_continuity() -> None:
    record = {
        "sensor": "bh1750",
        "value": None,
        "health": False,
        "unrelated_continues": True,
        "rebooted": False,
    }
    assert validate_faults([record]) == []
    assert validate_faults([{**record, "value": 0}])


def test_actuator_events_reject_unsafe_or_replayed_commands() -> None:
    assert validate_events([{"safe": True, "replayed": False, "clamped": True}]) == []
    assert validate_events([{"safe": False, "replayed": False}])


def test_soak_requires_sixty_minutes_and_known_interruptions() -> None:
    samples = [
        {"wall_s": 0, "uptime_ms": 0, "sequence": 1, "free_heap_bytes": 1000},
        {"wall_s": 3600, "uptime_ms": 3_600_000, "sequence": 2, "free_heap_bytes": 990},
    ]
    assert analyze(samples, interruptions=["backend_restart", "hotspot", "browser_restart"]) == []
    assert analyze(samples[:-1], interruptions=[])


def test_post_soak_database_integrity(tmp_path: Path) -> None:
    database = tmp_path / "telemetry.db"
    connection = sqlite3.connect(database)
    connection.execute("create table telemetry (id integer primary key)")
    connection.commit()
    connection.close()
    assert validate_database(database) == []


def test_resilience_gate_blocks_incomplete_hardware_evidence() -> None:
    result = evaluate({})
    assert result["eligible"] is False
    assert any("HIL evidence" in finding for finding in result["blockers"])
