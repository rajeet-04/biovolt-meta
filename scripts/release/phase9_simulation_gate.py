"""Pass the hardware-placeholder candidate without calling it a real release."""

import argparse
import json
from pathlib import Path


def evaluate(report: dict[str, object]) -> dict[str, object]:
    failures: list[str] = []
    if report.get("evidence_class") != "synthetic_demo":
        failures.append("simulation candidate must be labeled synthetic_demo")
    if report.get("hardware_hil") is not False:
        failures.append("simulation candidate must not claim hardware HIL")
    if int(report.get("minutes", 0)) < 60:
        failures.append("simulation smoke must cover 60 minutes")
    if int(report.get("frames", 0)) < 7201:
        failures.append("simulation smoke must include the expected cadence")
    if not report.get("fault") or int(report.get("fault_frames", 0)) <= 0:
        failures.append("simulation smoke must exercise a sensor fault")
    return {
        "status": "PASS" if not failures else "FAIL",
        "mode": "simulation",
        "hardware_release": False,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--fault", default="light_null")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    from simulation_smoke import run

    result = evaluate(run(minutes=args.minutes, fault=args.fault))
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
