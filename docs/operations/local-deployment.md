# Local production deployment

Copy `.env.example` to `.env`, replace the device token, and run `docker compose up -d`. Nginx is the only host-facing service; FastAPI, SQLite, and exports stay on the private Compose network and persistent `biovolt-data` volume.

For development ports, use `docker compose -f docker-compose.yml -f compose.dev.yml up -d` (`8080` Nginx, `8000` backend). The simulator is opt-in: `docker compose --profile simulator up -d`.

Check readiness with `scripts/check_stack_health.sh`. Never use `docker compose down -v` during a persistence check: removing the named volume destroys SQLite and exports.
