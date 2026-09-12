# Phase 9.4 implementation status

Review target: `origin/rajeet/phase-9.4` at `e2110aa`.

## Software completed in this review

- Independent comparison now uses a common overlap window, boundary
  interpolation, coverage thresholds, gap/reboot detection, positive passive
  denominator checks, and structured reasons.
- Independent analytics, claim traceability, and release-security validators
  have JSON report CLIs and tests.
- Python lint defects in the Phase 8 helper scripts are fixed.
- Full-suite acknowledgement tests use condition-based polling instead of a
  fixed 30 ms sleep.
- The demo runbook, storyboard, fallback cards, rehearsal record, release
  checklist, and freeze template now state exact visible checkpoints and
  evidence-class rules.

## Hardware or live-deployment gates still pending

These are intentionally not fabricated by software tests:

- ESP32 sensor/actuator HIL, reconnect, safety, and 30/60-minute soak.
- Trusted electrical/optical bench references and physical calibration run.
- Adaptive P&O wet experiment and measured Passive/Adaptive comparison.
- Three production cold starts, hotspot interruption, backend/browser restart,
  backup/restore, and offline rehearsal.
- Non-author product/judge/operator/recovery walkthrough, responsive and
  accessibility audit screenshots, and final evidence signoff.
- Live public-listener penetration check and proof that the deployed release
  exposes no mutation route or secret.

The simulation-only Phase 9 gate can pass with `hardware_release: false`; that
means the software candidate is validated, not that BioVolt is ready for a
measured hardware release. The final release gate must remain `FAIL` until the
machine-readable hardware/product/security evidence is supplied.
