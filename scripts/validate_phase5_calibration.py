#!/usr/bin/env python3
"""Independently recompute Phase 5 calibration values from exported JSON.

This intentionally contains no imports from ``biovolt_backend`` so it can
detect regressions in the production derivation helpers.
"""
import argparse
import json
import math
import sys
from pathlib import Path


def close(name: str, stored: object, calculated: float, tolerance: float) -> bool:
    if stored is None:
        return True
    ok = math.isclose(float(stored), calculated, rel_tol=tolerance, abs_tol=tolerance)
    print(f"{name}: stored={stored!r} recomputed={calculated:.12g} {'OK' if ok else 'MISMATCH'}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("revision", type=Path, help="calibration revision JSON export")
    parser.add_argument("--tolerance", type=float, default=1e-9)
    args = parser.parse_args()
    data = json.loads(args.revision.read_text())
    revision = data.get("revision", data)
    points = revision.get("biomass_points", revision.get("raw_calibration_points", []))
    if isinstance(points, str):
        points = json.loads(points)
    good = True
    if points:
        xs = [float(p.get("od680")) for p in points]
        ys = [float(p.get("dry_biomass_g_l")) for p in points]
        xbar, ybar = sum(xs) / len(xs), sum(ys) / len(ys)
        sxx = sum((x - xbar) ** 2 for x in xs)
        if len(points) < 3 or len(set(xs)) < 3 or sxx == 0:
            print("biomass fit: INELIGIBLE (need three distinct OD values)")
            good = False
        else:
            slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sxx
            intercept = ybar - slope * xbar
            residuals = [y - (slope * x + intercept) for x, y in zip(xs, ys)]
            ss_res = sum(r * r for r in residuals)
            ss_tot = sum((y - ybar) ** 2 for y in ys)
            r2 = None if ss_tot == 0 else 1 - ss_res / ss_tot
            rmse = math.sqrt(ss_res / len(points))
            good &= close("biomass_slope", revision.get("biomass_slope"), slope, args.tolerance)
            good &= close("biomass_intercept", revision.get("biomass_intercept"), intercept, args.tolerance)
            if r2 is not None:
                good &= close("biomass_r_squared", revision.get("biomass_r_squared"), r2, args.tolerance)
            good &= close("biomass_rmse_g_l", revision.get("biomass_rmse_g_l"), rmse, args.tolerance)
    electrical = revision.get("electrical_sample")
    if electrical:
        voltage = float(electrical["measured_voltage_mv"]) - float(revision["ads1115_offset_mv"])
        resistance = float(revision["load_resistance_ohm"])
        good &= close("corrected_voltage_mv", electrical.get("corrected_voltage_mv"), voltage, args.tolerance)
        good &= close("current_ua", electrical.get("current_ua"), voltage * 1000 / resistance, args.tolerance)
        good &= close("power_uw", electrical.get("power_uw"), voltage * voltage / resistance, args.tolerance)
    print("validation: PASS" if good else "validation: FAIL")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
