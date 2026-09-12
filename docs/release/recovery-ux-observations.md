# Recovery UX observations

Capture desktop and narrow/mobile production screens for backend/device
disconnected, stale, cached/offline, sensor unavailable, invalid calibration,
and public-tunnel unavailable states. For each, record the diagnosis, whether
data is live/stale/cached/unavailable, what remains safe, the next permitted
operator action, and the evidence required for recovery. Read-only judge mode
must not offer privileged recovery actions, and `Unavailable` must never be
rendered as zero.
