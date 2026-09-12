# Phase 3 HIL Smoke Checklist

This is a real-hardware acceptance procedure. The simulated-sensor build may
exercise transport first, but does not satisfy sensor/actuator HIL evidence.

```bash
docker compose stop simulator || true
docker compose --profile frontend up --build -d
curl http://localhost:8000/api/system/status
```

Within about 15 seconds of Wi-Fi availability, confirm the real device ID is
connected. Record 20 consecutive sequence values: normal increments are one
at roughly 500 ms. Keep the simulator stopped and verify the PWA renders the
device/cell, voltage/current/power, calibration-gated OD680, temperature, lux,
LED PWM, mixer state, Monitor mode, and fresh/live status.

