# Demo recovery cards

Use one card at a time. Keep the visible warning and evidence class unchanged.

## Backend restart

- Symptom/UI: backend disconnected or stale; no new telemetry is accepted.
- Actions: check `docker compose ps`; restart only the backend service and wait
  for `/api/health` before refreshing the local PWA.
- Do not: call stale cached data live or delete the persistent volume.
- Fallback: B/C if the backend does not recover in the runbook window.

## ESP32 reconnect

- Symptom/UI: device disconnected/stale; actuators must remain safe.
- Actions: verify power/Wi-Fi and reconnect the device; wait for authenticated
  WebSocket plus a fresh frame.
- Do not: issue repeated commands while the device is stale.
- Fallback: B/C, using measured history without claiming a current run.

## Hotspot/intermittent network

- Symptom/UI: local telemetry may become stale while the upstream route fails.
- Actions: restore the local LAN/hotspot; verify a fresh frame and device age.
- Do not: treat Cloudflared recovery as local system health.
- Fallback: C; local-only operation remains the preferred path.

## Stale dashboard

- Symptom/UI: `Stale`/`Disconnected`, cached data explicitly marked cached.
- Actions: inspect backend/device status, then refresh after fresh telemetry.
- Do not: narrate the last cached number as current.
- Fallback: B/C.

## Invalid calibration

- Symptom/UI: calibration or derived metric is `Unavailable` with a reason.
- Actions: select a valid immutable revision or show electrical values only.
- Do not: edit a historical revision or use a guessed coefficient.
- Fallback: B/C; keep biomass/CO2 unavailable.

## Sensor unavailable

- Symptom/UI: failed field is null/unavailable, health is false, unrelated
  sensors continue.
- Actions: use the fault card and continue with the valid fields.
- Do not: replace null with zero or reboot repeatedly for a routine fault.
- Fallback: B/C/D, labeled with the actual evidence class.

## Public tunnel failure

- Symptom/UI: optional public URL fails; local PWA/API remain healthy.
- Actions: use the local production URL or the measured history already loaded.
- Do not: expose the operator route publicly or weaken access controls.
- Fallback: A/B/C; no evidence-class change is needed.
