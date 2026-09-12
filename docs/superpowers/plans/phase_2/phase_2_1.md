# Phase 2.1: Frontend Foundation and Application Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the React/Vite/TypeScript PWA codebase with strict typing, Tailwind styling, routing, a reusable application shell, and test/lint/build tooling before backend integration begins.

**Architecture:** Keep the shell independent of telemetry logic. `app/` owns application wiring and routing, `components/layout/` owns navigation/layout primitives, pages are thin route targets, and design tokens live in Tailwind/CSS rather than inline constants.

**Tech Stack:** React, TypeScript, Vite, Tailwind CSS, React Router, Vitest, React Testing Library, ESLint.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- TypeScript strict mode is required.
- No telemetry formulas or backend science logic enters this module.
- No simulator-specific copy, IDs, imports, or route behavior.
- Only working Phase 2 routes are created: `/`, `/live`, `/charts`, `/system`.
- Future experiment/control/calibration routes are not stubbed as fake working screens.
- The visual direction follows the approved dark BioVolt dashboard concept with restrained green accents and high-contrast data presentation.

---

### Task 1: Bootstrap Vite React TypeScript package

**Files:**
- Create/replace: `frontend/package.json`
- Create: `frontend/package-lock.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/app/App.tsx`
- Create: `frontend/tests/app/test_bootstrap.tsx`

**Interfaces:**
- `App` renders the router/application shell.
- npm scripts: `dev`, `build`, `preview`, `test`, `test:run`, `typecheck`, `lint`.

- [ ] **Step 1: Write failing bootstrap render test**

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { App } from '../../src/app/App'


describe('App', () => {
  it('renders the BioVolt application title', () => {
    render(<App />)
    expect(screen.getByText('BioVolt')).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Define package dependencies**

Runtime dependencies must include:

```text
react
react-dom
react-router-dom
zustand
dexie
recharts
```

Development dependencies must include:

```text
vite
@vitejs/plugin-react
typescript
vitest
jsdom
@testing-library/react
@testing-library/jest-dom
@testing-library/user-event
eslint
@eslint/js
typescript-eslint
vite-plugin-pwa
tailwindcss
postcss
autoprefixer
```

Use a current mutually compatible version set at implementation time and commit the generated lockfile.

- [ ] **Step 3: Configure strict TypeScript and Vitest**

`tsconfig.app.json` must enable at least:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

Configure Vite test environment as `jsdom` and load `@testing-library/jest-dom` from a shared setup file.

- [ ] **Step 4: Implement minimal `App` and main entrypoint**

Render only a semantic application root and BioVolt title. Routing/layout arrives in later tasks.

- [ ] **Step 5: Install and verify**

```bash
cd frontend
npm install
npm run test:run
npm run typecheck
npm run build
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "chore: bootstrap BioVolt React PWA"
```

---

### Task 2: Add Tailwind theme and global visual tokens

**Files:**
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/styles/index.css`
- Modify: `frontend/src/main.tsx`
- Create: `frontend/src/components/layout/AppSurface.tsx`
- Create: `frontend/tests/components/test_app_surface.tsx`

**Interfaces:**
- `AppSurface({ children })` provides the global visual canvas.

- [ ] **Step 1: Write failing surface class/semantic test**

Render `AppSurface` and assert it renders a `main` landmark around children and uses the root `min-h-screen` layout class.

- [ ] **Step 2: Configure Tailwind content paths**

Include `index.html` and all `src/**/*.{ts,tsx}` files.

- [ ] **Step 3: Define CSS variables**

Use semantic variables such as:

```css
:root {
  --bg: 12 16 14;
  --panel: 20 26 22;
  --panel-strong: 27 35 30;
  --text: 235 244 238;
  --muted: 155 171 161;
  --accent: 74 222 128;
  --warning: 245 158 11;
  --danger: 239 68 68;
  --border: 52 66 57;
}
```

Do not scatter raw color literals throughout components.

- [ ] **Step 4: Add global typography and reduced-motion defaults**

Respect `prefers-reduced-motion` and keep animation nonessential.

- [ ] **Step 5: Run tests/build and commit**

```bash
npm run test:run
npm run build
git add frontend
git commit -m "feat: add BioVolt dashboard visual foundation"
```

---

### Task 3: Add router and application shell

**Files:**
- Create: `frontend/src/app/router.tsx`
- Create: `frontend/src/components/layout/AppShell.tsx`
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/TopBar.tsx`
- Create: `frontend/src/pages/OverviewPage.tsx`
- Create: `frontend/src/pages/LiveDataPage.tsx`
- Create: `frontend/src/pages/ChartsPage.tsx`
- Create: `frontend/src/pages/SystemPage.tsx`
- Modify: `frontend/src/app/App.tsx`
- Create: `frontend/tests/app/test_router.tsx`

**Interfaces:**
- `appRouter` defines `/`, `/live`, `/charts`, `/system`.
- `AppShell` renders navigation and an `<Outlet />`.

- [ ] **Step 1: Write failing route-navigation test**

Use a memory router and assert `/charts` renders `Charts` heading while keeping the BioVolt shell visible.

- [ ] **Step 2: Implement route definitions**

Each page must contain a real semantic heading and a concise Phase 2 description, not fake telemetry values.

- [ ] **Step 3: Implement sidebar navigation**

Exact Phase 2 links:

```text
Overview /
Live Data /live
Charts /charts
System /system
```

Do not add disabled fake links for experiments or controls.

- [ ] **Step 4: Add active-route styling and mobile menu state**

Navigation must be keyboard reachable. The mobile menu button requires an accessible name and `aria-expanded` state.

- [ ] **Step 5: Run route tests and commit**

```bash
npm run test:run
npm run typecheck
npm run build
git add frontend/src frontend/tests
git commit -m "feat: add BioVolt PWA application shell and routes"
```

---

### Task 4: Add ESLint and repository frontend commands

**Files:**
- Create: `frontend/eslint.config.js`
- Modify: `frontend/package.json`
- Modify: `frontend/README.md`
- Modify: root `README.md`

**Interfaces:**
- `npm run lint`
- `npm run typecheck`
- `npm run test:run`
- `npm run build`

- [ ] **Step 1: Configure ESLint for TypeScript/React**

Reject unused variables, accidental `any` where practical, unsafe React hook usage, and unreachable code.

- [ ] **Step 2: Document local startup**

```bash
cd frontend
npm install
npm run dev
```

State explicitly that backend integration is added in Phase 2.2 and that this module only proves the shell.

- [ ] **Step 3: Run full quality gate**

```bash
npm run lint
npm run typecheck
npm run test:run
npm run build
```

- [ ] **Step 4: Commit**

```bash
git add frontend root-or-readme-path
git commit -m "chore: enforce BioVolt frontend quality gates"
```

## Module 2.1 Exit Criteria

- [ ] React/Vite/TypeScript app builds successfully.
- [ ] TypeScript strict mode is active.
- [ ] Tailwind theme uses centralized semantic tokens.
- [ ] `/`, `/live`, `/charts`, and `/system` render through one application shell.
- [ ] Navigation is keyboard reachable and route-aware.
- [ ] No fake scientific values or future-feature routes are present.
- [ ] No simulator-specific frontend behavior exists.
- [ ] Tests, lint, typecheck, and production build pass.
