# BioVolt product brief

<!-- impeccable:product-schema 1 -->

## Platform

Web dashboard / installable PWA. The current delivery runs in a local browser
through the FastAPI backend and React frontend.

## Users

Inferred from the repository and operator workflows: researchers and bench
operators who need to confirm that a BioVolt device is connected, inspect
processed telemetry, review trends, and operate guarded controls.

## Product purpose

Inferred: make the state of a living biophotovoltaic prototype legible while it
is being developed, measured, and eventually moved from a simulator to ESP32
hardware.

## Product truth and constraints

- The dashboard receives backend-processed telemetry from a source-neutral
  device contract.
- The simulator is valid development infrastructure, but its values are
  synthetic and must remain visibly distinguishable from physical evidence.
- Current, power, cumulative energy, OD680, biomass, and estimated CO2 are
  backend-derived; OD680 is unavailable until valid optical references exist.
- Control and calibration are capability-gated and must communicate disabled,
  unsafe, unavailable, stale, and error states plainly.
- Hardware bench, parity, HIL, soak, and physical release evidence remain
  intentionally separate from the simulation-backed dashboard.

## Brand commitments

The product name is BioVolt. No existing visual system was supplied beyond the
current dark dashboard. The requested direction is professional, calm, direct,
and explicitly free of generic AI-dashboard decoration.

## Design principles

1. Show provenance and freshness before interpretation.
2. Give the operator a stable orientation and a clear next action.
3. Treat measurements as evidence, not decoration.
4. Use hierarchy and whitespace instead of a wall of identical cards.
5. Keep guarded actions visible without making them feel casually available.

## Accessibility and inclusion

The dashboard must work with keyboard focus, readable contrast, responsive
layouts, reduced motion preferences, and state text that does not depend on
color alone.

## Open questions

These facts are inferred for the redesign and should be confirmed when the
physical bench and final operator roles are defined: primary ambient-light
conditions, whether a dedicated operator role exists, and which controls need a
formal confirmation step.
