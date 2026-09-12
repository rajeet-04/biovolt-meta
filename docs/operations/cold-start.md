# Production cold start

Prepare `.env`, then run `docker compose up -d`. Run `scripts/phase8_cold_start.py` and confirm `/healthz` and `/api/health` are 200 before connecting hardware or enabling the simulator profile. Normal startup does not enable simulator or Cloudflared.
