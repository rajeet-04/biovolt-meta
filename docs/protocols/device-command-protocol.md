# Device Command Protocol v1

Commands and acknowledgements share the authenticated `/ws/device` connection
with telemetry but use separate schemas: `device-command.v1` travels from
FastAPI to the ESP32; `device-ack.v1` travels back.

FastAPI creates a UUID command, queues it, sends it, then records `accepted`,
`applied`, `rejected`, or `failed` only from the matching acknowledgement.
The supported commands are `set_mode`, `set_led_pwm`, `set_mixer`,
`request_status`, and `safe_stop`. `set_mode` carries monitor, passive, manual,
or adaptive; adaptive is contract-compatible but rejected as
`phase_not_available` until Phase 6.

Each command has server UTC `issued_at`/`expires_at` plus a bounded `ttl_ms`.
The backend never sends expired commands; the device rejects a command if its
receipt uptime plus TTL has elapsed before application. The same `command_id`
is idempotent: the device never repeats an actuator side effect and returns a
cached terminal acknowledgement when available. All successful writes remain
subject to firmware PWM, mixer-runtime, and cooldown safety limits.
