# Phase 5 calibration validation

Run the independent checker against an exported revision:

```bash
python scripts/validate_phase5_calibration.py revision.json
```

The checker recomputes the linear fit (slope, intercept, R², and RMSE) from
the saved raw biomass points without importing production calculation code. If
an electrical sample is included, it independently recomputes corrected
voltage, current, and power. A material mismatch exits non-zero.

Acceptance status: **Share with caveats** until a physical ADS1115/BPW34 path
and laboratory dry-biomass references are available. Simulator/native firmware
checks are valid for software behavior, but do not substitute for real sensor
calibration evidence.
