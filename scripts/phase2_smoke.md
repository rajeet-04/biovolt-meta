# Phase 2 PWA acceptance checklist

Operator runbook for verifying the Phase 2 PWA against the local backend and
simulator stack. These checks require a browser; service-worker and
installability behavior are not asserted by the shell scripts. Run them after
the Phase 1 stack is healthy.

## 1. Start the local stack

```bash
cp .env.example .env
# set BIOVOLT_DEVICE_SHARED_TOKEN to a long random value
docker compose --profile frontend --profile simulator up --build -d
```

Verify:

- [ ] `docker compose ps` shows `backend`, `frontend`, and `simulator` healthy
- [ ] `curl http://localhost:8000/api/health` returns `{"status": "ok"}`
- [ ] `curl http://localhost:8000/api/system/status` lists the simulator device

## 2. Live UI checks at http://localhost:4173

Open the PWA preview in a browser. Verify each item below:

- [ ] Overview page loads without console errors
- [ ] Source identifies the simulator (or the real device once wired)
- [ ] `ConnectionBadge` reads **"Backend connected"**
- [ ] Voltage, current, and power values appear and update
- [ ] Sequence number advances in the Live Data panel
- [ ] OD680 shows a value only when the backend has valid optical references
- [ ] Charts accumulate new samples as telemetry arrives
- [ ] System page reports backend and device status

## 3. Simulator-removal check

```bash
docker compose stop simulator
```

Verify:

- [ ] Frontend container remains up and serving `http://localhost:4173`
- [ ] Refreshing the PWA does not crash or blank the shell
- [ ] `ConnectionBadge` transitions to **"Backend disconnected"**; no
      simulator-specific UI logic is required to reach that state

Restart the simulator before continuing:

```bash
docker compose --profile simulator up --build -d
```

## 4. Offline PWA check

After the application shell has loaded once and the service worker is active:

1. Confirm the PWA is installable and launches as a standalone installed app
   from the laptop browser (browser address bar / app icon).
2. Disable external internet on the laptop (airplane mode or DNS block).
3. With the local stack still running, verify the PWA still shows live
   telemetry.
4. Stop the backend:

   ```bash
   docker compose stop backend
   ```

5. Refresh the installed/cached PWA. Verify:
   - [ ] App shell opens
   - [ ] Cached telemetry is explicitly labeled as cached or offline
   - [ ] No cached data is labeled live

Restart the backend when done:

```bash
docker compose up --build -d backend
```

## 5. Source-neutral hardware handoff

The same UI checks in steps 2-4 repeat against real `biovolt-01` telemetry.
The frontend must not require a code change to switch from the simulator to
the ESP32: stop the simulator, point the ESP32 at the laptop's
`ws://<laptop-hotspot-ip>:8000/ws/device` endpoint with the configured shared
token, and rerun the live and offline checks.

## 6. Commit

```bash
git add scripts/phase2_smoke.md README.md
git commit -m "docs: add Phase 2 PWA acceptance checklist"
```
