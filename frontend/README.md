# Frontend

BioVolt's frontend is a React, TypeScript, and Vite application. Phase 2.1
provides the installable-PWA foundation and application shell only: the
Overview, Live Data, Charts, and System shell routes share keyboard-reachable
navigation and centralized visual tokens.

Start the local development server:

```bash
cd frontend
bun install
bun run dev
```

Run the complete local quality gate from `frontend/`:

```bash
bun run lint
bun run typecheck
bun run test:run
bun run build
```

The frontend uses [bun](https://bun.sh/) for both dependency management
(`bun.lock`) and script execution (`bun run …`). Node/npm are not required.

Phase 2.1 does not connect to the backend or calculate telemetry. Backend
integration begins in Phase 2.2; scientific derivations remain owned by the
backend contract.

## Docker / preview proxy

`frontend/Dockerfile` builds the PWA and starts `vite preview` on port 4173.
Both the dev server and the preview server route `/api` and `/ws` through the
same proxy target, controlled by `BIOVOLT_PROXY_TARGET` (default
`http://localhost:8000`). The container sets
`BIOVOLT_PROXY_TARGET=http://backend:8000` so it can reach the FastAPI service
in `docker compose --profile frontend`. Override it with `--build-arg` or
`docker run -e BIOVOLT_PROXY_TARGET=...` to point at another host. For local
work without the full compose stack, run `BIOVOLT_PROXY_TARGET=… bun run
preview` to start the preview server with a custom proxy target.
