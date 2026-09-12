# Phase 7 analytics validation

`validate_phase7_analytics.py` is intentionally independent of production analytics code. It reads the exported CSV, validates explicit arm identity and mode, selects the shorter matched elapsed window, recomputes cumulative-energy deltas and gain, and reports coverage, gaps, reboots, evidence class, and eligibility.

```bash
python scripts/validate_phase7_analytics.py --csv experiment.csv --passive-arm passive --adaptive-arm adaptive --json
```

`gain_pct` is `(adaptive_energy_mj - passive_energy_mj) / passive_energy_mj * 100`. Null or ineligible values remain null; no significance or confidence language is inferred.
