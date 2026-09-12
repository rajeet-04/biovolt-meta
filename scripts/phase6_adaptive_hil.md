# Phase 6 Adaptive HIL acceptance

This is a procedure, not a claim of execution. No physical ESP32 is connected
in the current software-only validation environment.

Before power-up, set a conservative PWM envelope and verify Monitor-safe boot:
PWM 0, mixer OFF, and no Adaptive resume from NVS. Start only after a calibrated
experiment is selected and the applied command acknowledgement is visible.

Record sequence, uptime, raw BPV, PWM, optimizer direction, mode, network state,
and hold/fault observations for each perturb/settle/observe cycle. Verify every
request stays inside bounds, stale/invalid BPV enters Hold, Safe Stop ends
Adaptive ownership without a late PWM write, and reconnect restores telemetry.

Required scenarios: upper/lower bounds, invalid sensor recovery, backend/network
interruption, Adaptive-to-Manual/Monitor transition, Safe Stop, and a 30-minute
smoke with no reset, runaway perturb rate, or progressive heap loss.

Evidence status: simulator/native tests are passing; real-device HIL and the
30-minute smoke are pending. Synthetic response curves are test fixtures only,
not biological improvement evidence.
