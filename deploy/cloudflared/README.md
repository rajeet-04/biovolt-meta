# Optional public tunnel

Set a Cloudflare Tunnel token configured with origin `http://nginx:8081`, then start only with `docker compose --profile public up -d cloudflared`. The local stack has no dependency on this service.
