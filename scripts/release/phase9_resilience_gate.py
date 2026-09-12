"""Aggregate Phase 9.2 evidence into a machine-readable release decision."""

import argparse
import json
from pathlib import Path

try:
    from .analyze_soak import analyze
    from .validate_actuator_events import validate_events
    from .validate_cold_start import validate_runs
    from .validate_failures import validate_matrix
    from .validate_post_soak_data import validate_database
    from .validate_sensor_faults import validate_faults
except ImportError:  # Allow `python scripts/release/phase9_resilience_gate.py ...`.
    from analyze_soak import analyze
    from validate_actuator_events import validate_events
    from validate_cold_start import validate_runs
    from validate_failures import validate_matrix
    from validate_post_soak_data import validate_database
    from validate_sensor_faults import validate_faults


def evaluate(evidence: dict[str, object]) -> dict[str, object]:
    blockers: list[str] = []
    blockers.extend(validate_runs(evidence.get("cold_start", [])))
    blockers.extend(validate_matrix(evidence.get("failures", [])))
    blockers.extend(validate_faults(evidence.get("sensor_faults", [])))
    blockers.extend(validate_events(evidence.get("actuators", [])))
    soak = evidence.get("soak", {})
    if isinstance(soak, dict):
        blockers.extend(analyze(soak.get("samples", []), soak.get("interruptions", [])))
    else:
        blockers.append("soak evidence is missing")
    database = evidence.get("database")
    if database:
        blockers.extend(validate_database(Path(str(database))))
    else:
        blockers.append("post-soak database evidence is missing")
    blockers.extend(str(item) for item in evidence.get("ux_majors", []))
    if evidence.get("ux_audit_complete") is not True:
        blockers.append("recovery UX evidence is incomplete")
    if evidence.get("hil_complete") is not True:
        blockers.append("sensor/actuator HIL evidence is incomplete")
    return {"blockers": blockers, "majors": [], "eligible": not blockers}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.evidence.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2))
    return 0 if result["eligible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
