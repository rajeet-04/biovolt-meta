# Public read-only route policy

Nginx listener `:8081` is a separate public surface. It allows static PWA assets, `GET /api/*`, and `WS /ws/dashboard`; it rejects non-GET API methods and explicitly returns `403` for `/ws/device`. It overwrites client-supplied access headers with `X-BioVolt-Access-Mode: public_read_only`. Cloudflared targets only `http://nginx:8081`.

The operator listener on `:80` retains authenticated writes and the device WebSocket. Public access never exposes operator login, experiment/control/calibration mutations, or raw database files.
