# Phase 3.8: Hardware-in-the-Loop Soak, CI, Wiring Docs, and Phase Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Phase 3 with reproducible firmware CI, explicit wiring/configuration documentation, and a real-device hardware-in-the-loop acceptance procedure that proves the ESP32 can run continuously without simulator dependence.

**Architecture:** CI covers deterministic firmware compilation and native tests; physical sensor/actuator/network checks remain explicit local HIL gates. The acceptance sequence starts from a clean backend/PWA stack with simulator disabled, validates every sensor/health path, exercises disconnect/reconnect behavior, and finishes with a 30-minute soak.

**Tech Stack:** GitHub Actions, PlatformIO Core, ESP32 hardware, Docker Compose backend/PWA stack.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- CI must not require physical hardware or real secrets.
- HIL acceptance must use the real ESP32 with simulator stopped.
- No actuator load is energized before GPIO polarity and driver-stage wiring are bench-verified.
- A sensor disconnect test must degrade to null/false health, not crash/reboot.
- 30-minute soak must include backend/PWA telemetry observation.
- Final acceptance records evidence rather than relying on an undocumented visual check.

---

### Task 1: Add firmware GitHub Actions workflow

**Files:**
- Create: `.github/workflows/firmware.yml`

**Interfaces:**

Recommended workflow:

```yaml
name: ESP32 Firmware

on:
  push:
  pull_request:

jobs:
  firmware:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install platformio
      - run: pio test -d firmware/esp32 -e native
      - run: pio run -d firmware/esp32 -e esp32dev
```

- [ ] **Step 1: Add workflow**
- [ ] **Step 2: Run the same commands locally**

```bash
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
```

- [ ] **Step 3: Verify workflow contains no secret values**
- [ ] **Step 4: Commit**

```bash
git add .github/workflows/firmware.yml
git commit -m "ci: compile and test BioVolt ESP32 firmware"
```

---

### Task 2: Add hardware wiring document

**Files:**
- Create: `docs/hardware/esp32-wiring.md`

**Interfaces:**

Document this table:

```text
ESP32 GPIO 21  -> I2C SDA -> ADS1115 SDA + BH1750 SDA
ESP32 GPIO 22  -> I2C SCL -> ADS1115 SCL + BH1750 SCL
ESP32 GPIO 19  -> DS18B20 data with pull-up
ESP32 GPIO 25  -> 680 nm probe LED driver input
ESP32 GPIO 26  -> grow-light MOSFET/driver PWM input
ESP32 GPIO 27  -> mixer MOSFET/relay driver input
ADS1115 A0     -> BPV load-voltage measurement node
ADS1115 A1     -> BPW34 optical receiver front-end output
ADS1115 ADDR   -> 0x48
BH1750 ADDR    -> 0x23
```

- [ ] **Step 1: Add common-ground and supply notes**

State clearly which modules need common signal ground and that load power rails must be sized separately from ESP32 GPIO drive.

- [ ] **Step 2: Add pre-power checklist**

```text
verify GPIO-to-driver polarity
verify motor/LED load not on GPIO directly
verify I2C voltage compatibility
verify DS18B20 pull-up
verify ADS1115 input stays inside configured gain range
verify BPW34 analog front-end output range
verify common grounds where required
```

- [ ] **Step 3: Commit**

```bash
git add docs/hardware/esp32-wiring.md
git commit -m "docs: document BioVolt ESP32 wiring and pre-power checks"
```

---

### Task 3: Add firmware provisioning and bench checklist

**Files:**
- Create: `scripts/phase3_firmware_bench.md`

- [ ] **Step 1: Document build/upload**

```bash
cd firmware/esp32
pio run -e esp32dev -t upload
pio device monitor -b 115200
```

- [ ] **Step 2: Document provisioning sequence**

Use serial CLI:

```text
config set ssid <laptop-hotspot-ssid>
config set wifi_password <password>
config set backend_host <laptop-hotspot-ip>
config set backend_port 8000
config set device_id biovolt-01
config set cell_id cell-a
config set token <shared-token>
config save
reboot
```

- [ ] **Step 3: Document individual sensor bench checks**

ADS1115 A0:
- open circuit/known reference produces plausible raw + mV values.

Optical A1:
- probe LED visibly/photometrically pulses only around sample.
- changing optical path changes BPW34 raw count.

DS18B20:
- value is plausible and updates without stalling telemetry.

BH1750:
- covering sensor lowers lux.

- [ ] **Step 4: Document sensor disconnect behavior**

Disconnect each sensor one at a time and verify expected health field becomes false/null without rebooting the ESP32.

- [ ] **Step 5: Commit**

```bash
git add scripts/phase3_firmware_bench.md
git commit -m "docs: add BioVolt firmware bench verification checklist"
```

---

### Task 4: Add Phase 3 HIL smoke checklist

**Files:**
- Create: `scripts/phase3_hil_smoke.md`

- [ ] **Step 1: Start backend/PWA without simulator**

```bash
docker compose stop simulator || true
docker compose --profile frontend up --build -d
```

- [ ] **Step 2: Verify device connection within bounded time**

Within approximately 15 seconds after Wi-Fi is available:

```bash
curl http://localhost:8000/api/system/status
```

must list real device ID.

- [ ] **Step 3: Verify telemetry cadence**

Observe at least 20 consecutive incoming sequence values. Normal increments should be 1 with approximately 500 ms cadence.

- [ ] **Step 4: Verify PWA fields**

Check:

```text
real device/cell identity
voltage/current/power
OD680 only when backend calibration permits
temperature
lux
LED PWM
mixer state
mode=Monitor
fresh/live state
```

- [ ] **Step 5: Verify simulator remains unnecessary**

Confirm simulator container is stopped throughout the smoke run.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase3_hil_smoke.md
git commit -m "docs: add Phase 3 real-device HIL smoke checks"
```

---

### Task 5: Define 30-minute real-device soak

**Files:**
- Create: `scripts/phase3_hil_soak.md`

- [ ] **Step 1: Record baseline**

Record:

```text
ESP32 boot/reset reason
initial uptime
initial sequence
backend process health
initial latest telemetry timestamp
free heap from serial diagnostic
```

- [ ] **Step 2: Run for 30 minutes**

Every 5 minutes record:

```text
ESP32 uptime
latest sequence
Wi-Fi/WebSocket connected state
latest telemetry age
backend health
free heap
sensor health flags
actuator state
```

- [ ] **Step 3: Failure criteria**

Soak fails on any of:

```text
unexpected ESP32 reboot
backend crash
PWA live stream cannot recover
mixer/grow-light changes without planned request
sensor task stops advancing
telemetry remains stale >10 s while network is healthy
progressive free-heap collapse indicating leak
```

- [ ] **Step 4: Include one controlled backend restart during soak**

At approximately minute 10:

```bash
docker compose restart backend
```

ESP32 must reconnect without reboot; sequence gap and energy discontinuity logic must behave as Module 3.7 specifies.

- [ ] **Step 5: Include one short laptop-hotspot interruption**

Disable hotspot for about 10 seconds, restore it, then confirm sensing/actuator safety continued and telemetry returned.

- [ ] **Step 6: Commit**

```bash
git add scripts/phase3_hil_soak.md
git commit -m "docs: define 30-minute BioVolt hardware soak acceptance"
```

---

### Task 6: Run final Phase 3 regression and record PR evidence

**Files:**
- Modify: root `README.md`
- No protocol changes unless a separately reviewed contract defect is found.

- [ ] **Step 1: Run Phase 0 contract suite**

```bash
python scripts/validate_schemas.py
pytest tests/contracts -v
```

- [ ] **Step 2: Run Phase 1 backend suite**

```bash
cd backend
pytest -v
ruff check src tests
ruff format --check src tests
cd ..
```

- [ ] **Step 3: Run Phase 2 frontend suite**

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm run test:run
npm run build
cd ..
```

- [ ] **Step 4: Run firmware suite**

```bash
pio test -d firmware/esp32 -e native
pio run -d firmware/esp32 -e esp32dev
```

- [ ] **Step 5: Execute HIL bench, smoke, parity, and soak docs**

Run exactly:

```text
scripts/phase3_firmware_bench.md
scripts/phase3_hardware_parity.md
scripts/phase3_hil_smoke.md
scripts/phase3_hil_soak.md
```

- [ ] **Step 6: Record PR verification evidence**

PR notes must include:

```text
firmware compile result
native firmware test result
real ESP32 device ID
sensor health test result
backend reconnect result
hotspot reconnect result
30-minute soak start/end
unexpected reset count
final free heap
simulator remained stopped during HIL
Phase 0/1/2 regression results
```

- [ ] **Step 7: Update root README hardware status**

State that the real ESP32 path is verified only after the HIL checklist passes. Do not claim physical verification merely because firmware compiles.

- [ ] **Step 8: Commit documentation status**

```bash
git add README.md
git commit -m "docs: record BioVolt real-hardware Phase 3 workflow"
```

## Module 3.8 / Phase 3 Exit Criteria

- [ ] Firmware CI compiles ESP32 target and runs native tests.
- [ ] Wiring/pre-power checklist exists.
- [ ] Real sensor bench checks are documented and completed.
- [ ] Simulator is stopped for real-device HIL acceptance.
- [ ] Real ESP32 reaches backend and PWA.
- [ ] Sensor disconnects degrade gracefully.
- [ ] Backend restart and hotspot interruption recover without ESP32 reboot.
- [ ] 30-minute real-device soak passes.
- [ ] No unintended actuator activation occurs.
- [ ] Phase 0, Phase 1, Phase 2, and firmware regression suites are green.
