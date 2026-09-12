"""Run a fast, deterministic simulator soak for hardware-free release checks."""

import argparse
import json

from biovolt_simulator.generator import TelemetryGenerator

FAULT_FIELDS = {
    "temperature_null": ("environment", "temperature_c", "temperature_ok"),
    "light_null": ("environment", "lux", "light_sensor_ok"),
    "bpv_voltage_null": ("electrical", "bpv_voltage_mv", "ads1115_ok"),
    "bpw34_null": ("optical", "bpw34_raw", "bpw34_ok"),
}


def run(*, minutes: int = 60, fault: str | None = None) -> dict[str, object]:
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    if fault is not None and fault not in FAULT_FIELDS:
        raise ValueError(f"unsupported simulator fault: {fault}")
    generator = TelemetryGenerator(fault=fault)
    frames = int(minutes * 60 / 0.5) + 1
    previous_sequence = -1
    previous_uptime = -1
    fault_frames = 0
    for index in range(frames):
        frame = generator.next_frame(index * 0.5)
        if frame["sequence"] <= previous_sequence or frame["uptime_ms"] < previous_uptime:
            raise AssertionError("simulator sequence or uptime regressed")
        previous_sequence = int(frame["sequence"])
        previous_uptime = int(frame["uptime_ms"])
        if fault is not None:
            section, field, health_field = FAULT_FIELDS[fault]
            if frame[section][field] is not None or frame["health"][health_field] is not False:
                raise AssertionError("fault did not produce null value and false health")
            fault_frames += 1
    return {
        "evidence_class": "synthetic_demo",
        "hardware_hil": False,
        "minutes": minutes,
        "frames": frames,
        "fault": fault,
        "fault_frames": fault_frames,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=60)
    parser.add_argument("--fault", choices=sorted(FAULT_FIELDS))
    args = parser.parse_args()
    print(json.dumps(run(minutes=args.minutes, fault=args.fault), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
