# Public security matrix

Run `scripts/phase8_public_penetration.py --base-url http://localhost:8081`. Public GET health/telemetry/experiment/analytics reads may succeed; POST, PUT, PATCH, DELETE, operator auth, control, calibration writes, and `/ws/device` must return a deny response. `/ws/dashboard` is the only public WebSocket. Repeat with a spoofed `X-BioVolt-Access-Mode: operator` header and confirm capabilities remain read-only.
