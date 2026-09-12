# BioVolt controlled failure matrix

Record one JSON object per backend restart, Nginx restart, 20-second hotspot
interruption, upstream outage, Cloudflared stop/start, and browser refresh.
Include `scenario`, `recovery_s`, `state`, `safe`, and `replayed`. Local safety
must continue without upstream internet; stale/disconnected state must be shown
until fresh telemetry is received.
