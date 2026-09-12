# BioVolt design direction

<!--
THESIS: BioVolt is a lab signal board for watching a living energy system, not a
friendly KPI wall and not a gallery of metrics.
OWN-WORLD: Daylight paper and white surfaces, ink-black 2px rules, hard offset
shadows, electric blue structure, citrus-lime live status, and a disciplined
palette of purple, vermilion, orange, and teal chart signals.
STORY: Identify the source, read connection and freshness, scan live electrical
output, then explore a dense signal board without losing units, gaps, or truth.
FIRST VIEWPORT: An oversized overview title and source rail lead into a bold
electrical readout, operating-state block, and environment strip; Charts opens
as a colorful multi-signal live board.
FORM: Light brutalist lab console with minimal-maximal contrast: square edges,
hard shadows, tabular numerals, no gradients, no decorative glass, no invented
hardware or performance claims.
-->

## Visual system

- Use a warm near-white canvas with white panels, ink-black rules, and a very
  small number of hard offset shadows so the board feels physical and legible.
- Reserve electric blue for navigation and primary energy emphasis; use lime
  for live/healthy state, purple/teal/orange/vermilion for distinct signals,
  and keep warning/danger meanings explicit in text as well as color.
- Prefer square surfaces, 2px rules, and one pinned hard-shadow material level.
- Use the system sans stack for interface copy and tabular numerals for readings.
- Use one named kicker per page at most; let the large page title and a few
  structural blocks carry the hierarchy.
- Keep body copy to a readable measure and let dense telemetry use compact,
  labeled rows plus intentionally varied chart footprints rather than a wall of
  identical cards.

## Interaction rules

- Every control keeps a visible keyboard focus ring and communicates disabled,
  loading, stale, unavailable, and error states in text.
- Live state uses a compact square marker plus a label; do not rely on animation
  or color alone.
- Mobile collapses the navigation into the existing menu and lets telemetry
  groups stack without horizontal scrolling.
- Motion is limited to the existing first-load reveal and purposeful live data
  updates; `prefers-reduced-motion` removes authored motion and chart updates
  remain understandable without movement.

## Content rules

Use the product's language: source, freshness, live telemetry, derived, gated,
simulator, physical device, unavailable. Never imply that dummy data is a
hardware measurement.
