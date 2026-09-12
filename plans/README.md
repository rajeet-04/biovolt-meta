# Motion plans

These plans are the output of the `improve-animations` audit. They are
deliberately separate from the visual-theme implementation: the animation skill
is advisory and does not modify application source. Each plan names the
existing motion surface, the interaction reason for changing it, target values,
and a verification path.

## Order

1. [Live telemetry motion](./001-live-telemetry-motion.md) — stabilize live
   chart updates and make freshness perceptible without creating a distracting
   dashboard pulse.
