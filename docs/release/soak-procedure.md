# BioVolt 60-minute soak

Record observations at most five minutes apart from the first healthy frame
through 60 continuous minutes. Include uptime, sequence, free heap, network and
WebSocket state, sensor health, mode, actuator outputs, service health,
telemetry age, database size/rows, and container memory. Perform one backend
restart, one 20-second hotspot interruption, and one browser restart in their
specified windows. Analyze the JSONL observations with `analyze_soak.py` and
retain the resulting `soak-report.json` in the private release evidence pack.
