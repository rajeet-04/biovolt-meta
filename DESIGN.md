# BioVolt design direction

<!--
THESIS: BioVolt is an instrument console for watching a living energy system,
not a gallery of metrics.
OWN-WORLD: A dark graphite workbench with restrained ochre energy signals,
pale mint live status, tabular measurements, and quiet borders.
STORY: Orient the operator, establish source and freshness, make power legible,
then expose the supporting state and guarded actions.
FIRST VIEWPORT: A composed overview: source/status rail, one clear power readout,
electrical context, and operating state without a card wall.
FORM: Operate-mode console; deliberate columns, compact controls, no gradients,
no decorative glass, no invented hardware or performance claims.
-->

## Visual system

- Use deep graphite surfaces with a slight green cast to fit the product's
  biological/electrical context without resorting to neon.
- Reserve ochre for selected navigation and energy emphasis; reserve mint for
  live/healthy status; use amber and red only for their semantic states.
- Prefer 12px surface corners, 1px borders, and one soft elevation level.
- Use the system sans stack for interface copy and tabular numerals for readings.
- Use one named kicker per page at most; let headings and grouping carry the
  hierarchy.
- Keep body copy to a readable measure and let dense telemetry use compact,
  labeled rows rather than repeated equal-height cards.

## Interaction rules

- Every control keeps a visible keyboard focus ring and communicates disabled,
  loading, stale, unavailable, and error states in text.
- Live state uses a small status dot plus a label; do not rely on animation or
  color alone.
- Mobile collapses the navigation into the existing menu and lets telemetry
  groups stack without horizontal scrolling.
- Motion is limited to the live-state pulse and a short first-load reveal;
  `prefers-reduced-motion` removes both.

## Content rules

Use the product's language: source, freshness, live telemetry, derived, gated,
simulator, physical device, unavailable. Never imply that dummy data is a
hardware measurement.
