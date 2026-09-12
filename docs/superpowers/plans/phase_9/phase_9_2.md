# Phase 9.2: Cold-Start, Failure, and Soak Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove BioVolt remains safe and recoverable through the failure modes most likely during a hackathon demo and during a sustained hardware run.

**Architecture:** Automated acceptance covers container/process failures, persistence, and telemetry continuity; physical HIL procedures cover ESP32 power, hotspot loss, sensor removal, and actuator safety. The final soak combines both normal operation and controlled interruptions.

**Tech Stack:** Docker Compose, PlatformIO serial monitor/status output, production PWA, FastAPI health/status APIs, physical ESP32 and sensors.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Global Constraints
- ESP32 local safety/control continues when laptop/backend/network is unavailable.
- No stale control command is queued for later replay.
- Reconnect does not fabricate missing telemetry or energy.
- Hardware failure tests never bypass electrical/current limits or actuator safety constraints.
- Final release soak duration is exactly 60 minutes minimum, not optional.
- After a backend or hotspot path is restored, device WebSocket plus fresh telemetry must recover within 30 seconds or the drill fails.

---

### Task 1: Release cold-start drill

**Files:**
- Create: `docs/release/cold-start-drill.md`
- Create: `scripts/release/validate_cold_start.py`

Acceptance thresholds per run:
```text
Compose mandatory services healthy <= 60 s after command
ESP32 Wi-Fi connected <= 30 s after device power-on
/ws/device authenticated <= 60 s after device power-on
first valid telemetry persisted <= 75 s after device power-on
PWA state becomes live <= 90 s after device power-on
```

- [ ] Start from powered-down ESP32 and stopped production Compose stack.
- [ ] Start laptop hotspot and `docker compose up -d` using prepared `.env`.
- [ ] Power ESP32 and record time to Wi-Fi connection, device WebSocket, first valid telemetry, and PWA live state.
- [ ] Require all thresholds above to pass without upstream internet.
- [ ] Verify no actuator starts unexpectedly during boot.
- [ ] Repeat the drill three times; all three runs must pass.
- [ ] Commit `test: add BioVolt release cold-start drill`.

### Task 2: Controlled failure matrix

**Files:**
- Create: `docs/release/failure-matrix.md`
- Create: `scripts/release/validate_failures.py`

- [ ] Backend restart while ESP32 remains powered: verify no unsafe actuator change; after backend health returns, authenticated device WebSocket plus genuinely fresh telemetry must recover within 30 s.
- [ ] Nginx restart: verify backend persistence continues; after Nginx health returns, browser API/WebSocket access must recover within 15 s.
- [ ] Laptop hotspot off for 20 s then on: verify ESP32 sensing/control continues, telemetry gap is visible, and authenticated device telemetry recovers within 30 s of hotspot restoration.
- [ ] Upstream internet off/on: verify zero impact on local sensing, persistence, control, and PWA.
- [ ] Cloudflared stop/start: verify zero impact on local operation.
- [ ] Browser/PWA refresh during active monitoring: verify state reload without command replay and live state returns within 10 s when backend/device are healthy.
- [ ] Record expected user-visible state for each failure and recovery.
- [ ] Commit `test: validate BioVolt release failure matrix`.

### Task 3: Sensor fault HIL checks

**Files:**
- Create: `docs/release/sensor-fault-drill.md`

- [ ] Disconnect DS18B20 and verify `temperature_c=null`, health false, no ESP32 reboot.
- [ ] Disconnect BH1750 and verify `lux=null`, health false.
- [ ] Disconnect/interrupt ADS1115 path and verify electrical/optical health behavior follows Phase 3 rules.
- [ ] Verify the PWA renders unavailable values rather than zero or fabricated values.
- [ ] Restore each sensor and verify recovery without full-system restart where supported.
- [ ] Record any fault that can affect adaptive operation and verify safety/control fallback.
- [ ] Commit `test: document BioVolt sensor fault release drill`.

### Task 4: Actuator safety HIL checks

**Files:**
- Create: `docs/release/actuator-safety-drill.md`

- [ ] Verify boot state: grow LED PWM 0, mixer off, monitor mode.
- [ ] Attempt out-of-range PWM command and verify firmware clamps/rejects according to the Phase 3 safety policy.
- [ ] Run mixer to maximum runtime and verify forced off at the configured limit, with timing tolerance no greater than 250 ms beyond the firmware task/check interval.
- [ ] Attempt mixer restart during cooldown and verify rejection.
- [ ] Disconnect backend during active/manual operation and verify local safety remains authoritative.
- [ ] Trigger adaptive/manual ownership transitions and verify no conflicting actuator writer exists.
- [ ] Classify any unsafe behavior as BLOCKER.
- [ ] Commit `test: validate BioVolt actuator safety HIL`.

### Task 5: 60-minute hardware soak with controlled interruptions

**Files:**
- Create: `scripts/release/record_soak.py`
- Create: `docs/release/soak-procedure.md`

**Required duration:** at least 60 continuous minutes from first healthy telemetry frame to final sample.

- [ ] Record every 5 minutes: ESP32 uptime, sequence, free heap, Wi-Fi state, WebSocket state, sensor health, actuator state, backend health, telemetry age, DB row growth.
- [ ] Include one backend restart between minute 15 and minute 25.
- [ ] Include one 20-second hotspot interruption between minute 30 and minute 40.
- [ ] Include one browser/PWA restart between minute 45 and minute 55.
- [ ] After each backend/hotspot restoration, require authenticated device WebSocket plus fresh telemetry within 30 s.
- [ ] Verify no unexplained ESP32 reboot, runaway actuator, progressive heap collapse, corrupt DB rows, or permanently stale dashboard.
- [ ] Treat progressive free-heap loss greater than 10% from the stabilized 5-minute baseline, without later recovery, as MAJOR pending investigation.
- [ ] Verify telemetry sequence gaps correspond to observed interruptions and are not hidden.
- [ ] Produce `soak-report.json` for the release evidence pack.
- [ ] Commit `test: add BioVolt release hardware soak`.

### Task 6: Resilience release gate

**Files:**
- Create: `scripts/release/phase9_resilience_gate.py`

- [ ] Aggregate cold-start, failure, sensor fault, actuator safety, and soak results.
- [ ] Require zero unsafe actuator events.
- [ ] Require zero unexplained reboot/data-corruption events.
- [ ] Require every planned backend/hotspot recovery to meet the 30 s device-telemetry recovery limit.
- [ ] Require the full 60-minute soak duration.
- [ ] Classify unrecoverable core failures as MAJOR or BLOCKER per Phase 9 overview.
- [ ] Commit `test: add BioVolt resilience release gate`.

## Exit Criteria
- [ ] Three cold-start runs pass exact readiness thresholds without internet.
- [ ] Backend/Nginx/hotspot/internet/Cloudflared/browser interruptions recover within their defined thresholds.
- [ ] Sensor faults are represented explicitly and do not fabricate values.
- [ ] Actuator safety holds during disconnects and invalid commands.
- [ ] 60-minute final soak passes with no BLOCKER/MAJOR resilience issue.
