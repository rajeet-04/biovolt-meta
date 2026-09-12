# Phase 9.2: Cold-Start, Failure, Hardware-Safety, and Soak Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan task-by-task. Apply Ponytail product-design reasoning to every real failure/recovery state observed during HIL and production drills. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove BioVolt remains safe, truthful, and recoverable through the failure modes most likely during a hackathon demo and during a sustained real-hardware run.

**Architecture:** Automated acceptance covers container/process failures, persistence, and telemetry continuity. Physical HIL procedures cover ESP32 power, hotspot loss, sensor removal, and actuator safety. The final soak combines normal operation and controlled interruptions. Every technical failure has a corresponding PWA state assertion so a technically safe system cannot pass while visually misrepresenting stale or failed data.

**Tech Stack:** Docker Compose, PlatformIO serial/status output, production PWA, FastAPI health/status APIs, physical ESP32 and sensors, Python release scripts.

**Spec:** `docs/superpowers/plans/phase_9/phase_9_0.md`

## Frozen Release Thresholds

```text
Compose mandatory services healthy <= 90 s
ESP32 authenticated device WebSocket + fresh telemetry after path restored <= 30 s
Nginx browser path recovery after Nginx health <= 15 s
healthy-network telemetry silence failure > 10 s
PWA Live state only after genuinely fresh telemetry
final real-hardware soak >= 60 continuous min
soak observation interval <= 5 min
unexpected ESP32 reboot = 0
actuator safety violation = 0
stale command replay = 0
data corruption/loss = 0
```

Free-heap guard after 5-minute warmup:
- final free heap >= 85% of stabilized baseline unless a documented one-time allocation explains the change
- no sustained monotonic downward trend across repeated observations
- progressive loss >10% without recovery is MAJOR pending investigation even before 85% threshold is crossed

Do not relax these after observing results.

---

### Task 1: Release cold-start drill

**Files:**
- Create: `docs/release/cold-start-drill.md`
- Create: `scripts/release/validate_cold_start.py`

Sequence:

```text
ESP32 off + production stack stopped
-> start laptop hotspot
-> docker compose up -d
-> PWA shows waiting/disconnected truthfully
-> power ESP32
-> Wi-Fi connects
-> /ws/device authenticates
-> valid telemetry persists
-> PWA becomes Live
```

- [ ] Run without upstream internet.
- [ ] Require mandatory containers healthy <=90 s.
- [ ] Require device WebSocket + fresh telemetry within 30 s of network/backend availability after normal boot provisioning settles.
- [ ] Verify no actuator starts unexpectedly during boot.
- [ ] Verify no fake/old live metrics appear before device telemetry.
- [ ] Repeat three times; all runs pass.
- [ ] Save timing report to release evidence.
- [ ] Commit `test: add BioVolt release cold-start drill`.

---

### Task 2: Controlled service/network failure matrix

**Files:**
- Create: `docs/release/failure-matrix.md`
- Create: `scripts/release/validate_failures.py`

Scenarios:

**Backend restart**
- local firmware safety continues
- PWA moves to stale/backend-disconnected
- device reconnect + fresh telemetry <=30 s after backend available
- no missing-interval energy integration
- no stale write replay

**Nginx restart**
- backend persistence continues
- browser/device proxy paths recover
- browser path usable <=15 s after Nginx health

**Laptop hotspot off for 20 s**
- ESP32 remains powered
- Sensor/Control/Actuator tasks continue
- sequence gap becomes visible
- fresh device telemetry <=30 s after hotspot restoration

**Upstream internet off/on**
- zero core local impact

**Cloudflared stop/start**
- zero local impact

**Browser/PWA refresh**
- no command replay
- fresh state restored from backend/device truth

- [ ] Record technical result and user-visible state for each scenario.
- [ ] Commit `test: validate BioVolt release failure matrix`.

---

### Task 3: Sensor fault HIL checks

**Files:**
- Create: `docs/release/sensor-fault-drill.md`
- Create: `scripts/release/validate_sensor_faults.py`

Where electrically safe, disconnect/reconnect:
- DS18B20
- BH1750
- ADS1115/BPV path
- BPW34 optical path

Expected:

```text
failed sensor
-> corresponding value null/unavailable
-> health false
-> no fabricated zero
-> unrelated acquisition continues
-> derived eligibility updates truthfully
-> PWA identifies unavailable data
```

- [ ] Verify no ESP32 reboot from routine sensor loss.
- [ ] Verify DS18B20 loss yields `temperature_c=null`.
- [ ] Verify BH1750 loss yields `lux=null`.
- [ ] Verify optical failure makes OD680/biomass/CO2 unavailable when required.
- [ ] Verify sensor recovery where supported without full-system restart.
- [ ] Commit `test: validate BioVolt sensor fault release drill`.

---

### Task 4: Actuator safety HIL checks

**Files:**
- Create: `docs/release/actuator-safety-drill.md`
- Create: `scripts/release/validate_actuator_events.py`

- [ ] Verify boot state: grow LED PWM safe/off, mixer off, monitor/safe baseline.
- [ ] Attempt below/above-range PWM and verify clamp/rejection according to firmware policy.
- [ ] Run mixer to maximum runtime and verify forced off within firmware timing tolerance.
- [ ] Attempt mixer restart during cooldown and require rejection.
- [ ] Disconnect backend during active/manual operation and verify local safety remains authoritative.
- [ ] Exercise Adaptive -> Manual/Stop ownership transition and verify optimizer cannot continue writing after preemption.
- [ ] Record command IDs/ACK/rejection and resulting actuator telemetry.
- [ ] Classify any unsafe behavior as BLOCKER.
- [ ] Commit `test: validate BioVolt actuator safety HIL`.

---

### Task 5: Ponytail real-failure comprehension audit

**Files:**
- Create: `docs/release/recovery-ux-observations.md`
- Evidence: `release-evidence/screenshots/failure-states/`

During Tasks 2-4 capture production screens for:
- backend disconnected
- device disconnected
- stale telemetry
- cached/offline
- sensor unavailable
- invalid calibration/derived metric unavailable
- public tunnel unavailable while local stack is healthy

For each state answer:

```text
What failed?
Is currently displayed data live, stale, cached, or unavailable?
What remains safe/available?
What is the next useful operator action?
Does recovery become visible only after real healthy evidence?
```

Ponytail acceptance:
- one dominant diagnosis per failure state
- no contradictory banners
- no raw stack trace as primary UI
- technical details can remain in diagnostics/log view
- read-only judge mode never suggests a recovery action requiring operator privileges
- `Unavailable` is not presented as zero

- [ ] Capture desktop and at least one narrow/mobile state for critical failures.
- [ ] Classify misleading live/stale/recovery presentation as MAJOR.
- [ ] Commit `docs: add Ponytail BioVolt real-failure UX audit`.

---

### Task 6: 60-minute real-hardware soak with controlled interruptions

**Files:**
- Create: `scripts/release/record_soak.py`
- Create: `scripts/release/analyze_soak.py`
- Create: `docs/release/soak-procedure.md`

**Required duration:** >=60 continuous minutes from first healthy telemetry frame to final sample.

Record <= every 5 minutes:

```text
wall-clock time
ESP32 uptime_ms
sequence
free_heap_bytes
Wi-Fi state
WebSocket state
sensor health
mode
LED PWM
mixer state
backend/Nginx health
telemetry age
DB row count/file size
container memory
```

Controlled interruptions:
- one backend restart between minute 15-25
- one 20-second hotspot interruption between minute 30-40
- one browser/PWA restart between minute 45-55

Failure conditions:
- unexpected ESP32 reboot
- actuator safety violation
- healthy-network telemetry silence >10 s
- unrecovered backend/Nginx failure
- corrupt persistence
- progressive free-heap collapse
- unbounded process/browser growth pattern
- stale/cached state shown as live

- [ ] Establish stabilized 5-minute heap baseline.
- [ ] Execute all controlled interruptions.
- [ ] Require each backend/hotspot recovery to meet 30 s device/fresh-telemetry limit.
- [ ] Verify sequence gaps correspond to known interruptions and are not hidden.
- [ ] Verify final experiment/history/export remains readable.
- [ ] Emit `soak-report.json`.
- [ ] Commit `test: add BioVolt release hardware soak`.

---

### Task 7: Persistence and continuity review after soak

**Files:**
- Create: `scripts/release/validate_post_soak_data.py`

- [ ] Verify SQLite integrity check passes.
- [ ] Verify no duplicate/invalid experiment identity caused by restarts.
- [ ] Verify calibration revision references remain resolvable.
- [ ] Verify energy accumulator did not bridge controlled sequence gaps.
- [ ] Verify completed experiment exports regenerate/read correctly.
- [ ] Commit `test: validate BioVolt post-soak persistence integrity`.

---

### Task 8: Resilience release gate

**Files:**
- Create: `scripts/release/phase9_resilience_gate.py`

Aggregate:
- cold start
- controlled failure matrix
- sensor faults
- actuator safety
- Ponytail failure-state audit
- soak
- post-soak persistence

- [ ] Require zero actuator safety events.
- [ ] Require zero unexplained reboot/data-corruption events.
- [ ] Require all planned network/service recovery thresholds.
- [ ] Require full 60-minute soak.
- [ ] BLOCKER on unsafe actuator behavior, data corruption, or core internet dependency.
- [ ] MAJOR on misleading failure-state UX, unreliable reconnect, or resource degradation.
- [ ] Require zero BLOCKER and zero MAJOR findings.
- [ ] Commit `test: add BioVolt resilience release gate`.

## Exit Criteria

- [ ] Three cold starts pass without internet.
- [ ] Backend/Nginx/hotspot/internet/Cloudflared/browser interruptions recover within defined thresholds.
- [ ] Sensor faults are explicit and never fabricate readings.
- [ ] Actuator safety holds through invalid commands and disconnects.
- [ ] Failure/recovery UX communicates technical truth.
- [ ] 60-minute real-hardware soak passes.
- [ ] Post-soak data/provenance integrity passes.
- [ ] Zero BLOCKER and zero MAJOR resilience findings remain.
