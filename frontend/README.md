# Frontend

BioVolt's frontend is a React, TypeScript, and Vite application. Phase 2.1
provides the installable-PWA foundation and application shell only: the
Overview, Live Data, Charts, and System shell routes share keyboard-reachable
navigation and centralized visual tokens.

Start the local development server:

```bash
cd frontend
npm install
npm run dev
```

Run the complete local quality gate from `frontend/`:

```bash
npm run lint
npm run typecheck
npm run test:run
npm run build
```

Phase 2.1 does not connect to the backend or calculate telemetry. Backend
integration begins in Phase 2.2; scientific derivations remain owned by the
backend contract.
