# Operator recovery card

1. Backend disconnected: inspect container health and restart backend using Compose.
2. Device disconnected: check power/hotspot and reconnect the device or explicit simulator.
3. Stale data: stop relying on live values until a fresh timestamp appears.
4. Public tunnel down: continue local operation; restart Cloudflared separately.
5. Unavailable comparison: inspect quality/provenance and export evidence; never substitute a synthetic result.
