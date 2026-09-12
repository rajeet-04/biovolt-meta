# Analytics validation

This is a three-way comparison, not a screenshot-only check:

```text
exported raw samples -> independent recomputation -> captured API JSON -> PWA headline
```

1. Export the selected passive/adaptive experiment rows from the local API. Do
   not edit the export or replace null values with zero.
2. Create a small JSON input with `passive`, `adaptive`,
   `passive_evidence`, and `adaptive_evidence`. Each sample is
   `[uptime_ms, power_uw]`.
3. Recompute independently:

   ```powershell
   uv run python scripts/release/recompute_experiment_comparison.py comparison-input.json --output independent.json
   ```

4. Save the exact production comparison response as `production.json`, then
   compare it with the independent result:

   ```powershell
   uv run python scripts/release/validate_production_analytics.py independent.json production.json --output analytics-recompute.json
   ```

The validator checks the frozen Phase 9.4 tolerances, common duration,
coverage, evidence class, eligibility, negative gains, and structured
ineligibility reasons. A `FAIL` result is a release blocker. The UI check is
manual: the Results headline must show the same value/rounding or the same
`Unavailable` reason as the API, with no fabricated zero.
