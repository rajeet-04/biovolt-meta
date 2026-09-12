# Release-candidate checklist

The final gate is binary. Missing evidence produces `FAIL`, never a warning-only
success. Supply machine-readable reports for:

- Phase 9.1 scientific validation and copy checks.
- Phase 9.2 resilience, safety, cold-start, soak, and HIL evidence.
- Phase 9.3 judge/operator/recovery, responsive, accessibility, and screenshot
  audits.
- Phase 8 public-route/security acceptance.
- Independent analytics comparison and claim traceability.
- Contract, backend, frontend, simulator, and firmware CI.

Run `scripts/release/phase9_release_gate.py evidence.json`. Release requires
`status: PASS`, zero `BLOCKER` and `MAJOR` findings, and a secret-safe evidence
index. The simulation-only gate is useful for software readiness but does not
substitute for hardware HIL or a measured-performance release.
