# Phase 3 Device Parity Checklist

Use the simulator-backed firmware placeholder until the sensor bench is ready;
it sends the same raw schema, headers, and WebSocket path as the real drivers.

1. Start the backend and PWA without the simulator container:

   ```bash
   docker compose stop simulator || true
   docker compose --profile frontend up --build -d
   ```

2. Provision the ESP32 with the actual hotspot SSID/password, backend IP and
   port, `biovolt-01`, `cell-a`, and the backend shared token. Save and reboot.
3. Confirm the source-neutral connection and processed telemetry:

   ```bash
   curl http://localhost:8000/api/system/status
   curl "http://localhost:8000/api/telemetry/latest?device_id=biovolt-01&cell_id=cell-a"
   ```

4. Verify increasing sequence values, backend-derived current/power, valid
   OD680 only with backend references, and `control.mode == "monitor"`.
   Processed telemetry must not include `optimizer_direction`; the raw firmware
   serializer test verifies it remains `0` in monitor mode.
5. Verify the existing PWA shows the device/cell without a simulator/hardware
   branch or rebuild.
6. For an outage test, record sequence, uptime, and cumulative energy; stop
   the backend for 15 seconds while keeping the ESP32 powered; restart it; then
   record the first and second post-gap frames. The first preserves cumulative
   energy and the second resumes normal integration.

`uint32_t` sequence wraparound is intentionally outside Phase 3: at 2 Hz it
takes decades. A lower uptime is the reboot signal for this release.
