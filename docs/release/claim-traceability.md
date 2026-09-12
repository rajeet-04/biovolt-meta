# Claim traceability

Keep a JSON array for every headline spoken or shown in the demo. Validate it
before the final gate:

```powershell
uv run python scripts/release/validate_claim_traceability.py claims.json --output claim-traceability.json
```

Each entry contains `claim`, `ui_field`, `api_field`, `experiment`,
`evidence_class`, and `source`. Claims derived from calibration also include
`requires_calibration: true` and the immutable `calibration_revision`.
Synthetic entries must include `synthetic_label: "synthetic_demo"`. A missing
trace makes that claim unavailable; it must not be repaired with a guessed
number. Historical measured results stay labeled as historical rather than
being presented as the current live run.
