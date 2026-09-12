# Recovery-state audit

Backend loss must show `Backend disconnected`; old telemetry must show `Stale telemetry`; ESP32 loss must show `Device disconnected`; cached shell/data must show `Showing cached data`; quality failure must show `Unavailable` with a reason. Each state has one dominant message and a runbook action. Recovery returns to `Live` only after a newer valid telemetry timestamp arrives.
