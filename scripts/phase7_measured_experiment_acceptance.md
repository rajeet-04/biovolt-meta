# Measured experiment acceptance record

Use one copy of this template per judge-facing comparison. A result is eligible only when the evidence class is `measured`, both arm quality gates pass, and backend and independent validator values agree within the documented numerical tolerance.

```text
experiment_id:
passive_arm_id:
adaptive_arm_id:
evidence_class:
passive_calibration_revision_id:
adaptive_calibration_revision_id:
passive_baseline_sequence/time:
adaptive_baseline_sequence/time:
common_duration_s:
passive_power_coverage:
adaptive_power_coverage:
passive_gap_fraction/max_gap:
adaptive_gap_fraction/max_gap:
passive_matched_energy_mj:
adaptive_matched_energy_mj:
backend_gain_pct:
independent_gain_pct:
absolute/relative_validation_difference:
scientific_outcome_eligibility:
biomass_extrapolation_flags:
known_caveats:
result_status: eligible | ineligible
```

Negative gains remain negative. Ineligible results show their reason. Synthetic results are never substituted for measured evidence without persistent synthetic labeling.
