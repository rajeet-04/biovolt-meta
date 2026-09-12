# Pre-demo checklist

- Verify `docker compose up -d` and health checks.
- Confirm the local PWA identifies live/stale/device/backend status truthfully.
- Confirm the selected evidence class and completed Results route.
- Confirm a safe CSV export and a backup of the persistent data volume.
- If using simulation, start it explicitly with `--profile simulator` and keep `Simulation / demo data` visible.
- If using public access, start Cloudflared separately with `--profile public`; verify local operation remains healthy when it stops.
