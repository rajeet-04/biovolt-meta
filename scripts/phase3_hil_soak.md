# Phase 3 Thirty-Minute HIL Soak Record

This record is incomplete until run with a real ESP32, simulator stopped, and
the actual sensor/driver bench connected.

Record boot/reset reason, initial uptime/sequence, backend health, latest
telemetry timestamp, and free heap before starting. Every five minutes for 30
minutes record uptime, sequence, Wi-Fi/WebSocket state, telemetry age, backend
health, free heap, sensor health flags, and actuator state.

At about minute 10 run:

```bash
docker compose restart backend
```

Confirm the ESP32 reconnects without reboot, the first post-gap energy value
does not jump, and the next contiguous frame resumes integration. Also disable
the hotspot for about 10 seconds, restore it, and verify sensing/actuator
safety continued before telemetry returned.

Fail the soak on any unexpected reset, backend crash, unrecoverable PWA stream,
unplanned actuator change, halted sensor task, telemetry stale for more than
10 seconds on a healthy network, or progressive free-heap collapse.
