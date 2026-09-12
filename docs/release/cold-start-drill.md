# BioVolt cold-start drill

Run three times with upstream internet disabled. Start the local stack, confirm
mandatory services are healthy within 90 seconds, then boot the ESP32 and record
the first authenticated WebSocket and fresh telemetry frame. Recovery must be
within 30 seconds, the boot actuator state must be safe, and the PWA must remain
waiting/disconnected until the fresh frame arrives. Store runs in the resilience
evidence JSON under `cold_start`.
