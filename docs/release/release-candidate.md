# BioVolt release candidate

This is a freeze template, not a release declaration. Populate it only after
`phase9_release_gate.py` reports `PASS`:

```text
git_revision:
firmware_version:
backend_version:
frontend_version:
schema_versions:
calibration_revisions:
startup_command:
environment_preparation:
known_minor_limitations:
evidence_index:
```

Keep tokens, PINs, Wi-Fi credentials, screenshots containing private data, and
private attestations outside the repository evidence index. A simulation-only
report must remain labeled `synthetic_demo` and cannot populate a measured
release claim.
