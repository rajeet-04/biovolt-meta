# Phase 4.5: Operator PIN Session and PWA Experiment/Control UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Protect all state-changing experiment/control actions with a lightweight operator session and add PWA workflows that clearly distinguish operator intent from device-confirmed hardware state.

**Architecture:** FastAPI stores only a password hash plus short-lived opaque server-side sessions. The PWA uses same-origin HttpOnly cookies and never stores the operator PIN/session token in IndexedDB or localStorage. UI write actions return command resources and subscribe/poll until the device acknowledgement establishes a terminal command state.

**Tech Stack:** FastAPI, `argon2-cffi`, secure opaque cookies, React Router, TypeScript, Zustand, React Testing Library, Vitest.

**Spec:** `docs/architecture/software-architecture.md`

## Global Constraints

- No user accounts, registration, OAuth, password reset, roles, or JWT framework.
- Operator PIN hash comes from backend environment as `BIOVOLT_OPERATOR_PIN_HASH`.
- PIN plaintext is never logged or persisted.
- Session cookie is `HttpOnly`, `SameSite=Strict`, and `Secure` when served over HTTPS.
- Phase 4 session maximum lifetime is 30 minutes.
- Backend restart may invalidate sessions.
- Read-only telemetry pages remain usable when logged out.
- Write routes return `401` or `403` without a valid operator session.
- PWA must never show optimistic `applied` state before device ack.
- Cached/offline PWA state may show historical command records but must not queue actuator commands for later delivery.
- Control actions are disabled when backend is disconnected or selected device is stale.

---

### Task 1: Add operator security settings and PIN verification

**Files:**
- Modify: `backend/src/biovolt_backend/config.py`
- Create: `backend/src/biovolt_backend/security/operator.py`
- Create: `backend/src/biovolt_backend/security/__init__.py`
- Test: `backend/tests/security/test_operator.py`

**Interfaces:**

```python
class OperatorAuthenticator:
    def verify_pin(self, pin: str) -> bool: ...
```

- [ ] **Step 1: Add `operator_pin_hash` setting with no default secret**
- [ ] **Step 2: Write correct/incorrect PIN verification tests using an Argon2 test hash**
- [ ] **Step 3: Implement constant library verification through `argon2.PasswordHasher.verify`**
- [ ] **Step 4: Verify logs/config repr redact the hash**
- [ ] **Step 5: Run and commit**

```bash
cd backend
pytest tests/security/test_operator.py -v
git add src/biovolt_backend/config.py src/biovolt_backend/security tests/security/test_operator.py
git commit -m "feat: verify BioVolt operator PIN securely"
```

---

### Task 2: Add in-memory expiring operator session store

**Files:**
- Create: `backend/src/biovolt_backend/security/sessions.py`
- Test: `backend/tests/security/test_sessions.py`

**Interfaces:**

```python
class OperatorSessionStore:
    def create(self, now: datetime) -> tuple[str, datetime]: ...
    def valid(self, token: str, now: datetime) -> bool: ...
    def revoke(self, token: str) -> None: ...
    def prune(self, now: datetime) -> int: ...
```

Implementation:
- token: `secrets.token_urlsafe(32)`
- store only SHA-256 digest as dictionary key
- absolute expiry = creation + 30 minutes

- [ ] **Step 1: Write create/valid/expiry/revoke tests with fixed time**
- [ ] **Step 2: Implement digest-keyed store**
- [ ] **Step 3: Add prune test**
- [ ] **Step 4: Run and commit**

```bash
pytest tests/security/test_sessions.py -v
git add src/biovolt_backend/security/sessions.py tests/security/test_sessions.py
git commit -m "feat: add expiring BioVolt operator sessions"
```

---

### Task 3: Add operator session API and write dependency

**Files:**
- Create: `backend/src/biovolt_backend/api/operator.py`
- Create: `backend/src/biovolt_backend/security/dependencies.py`
- Modify: `backend/src/biovolt_backend/main.py`
- Test: `backend/tests/api/test_operator.py`

**Routes:**

```text
POST /api/operator/login   body {"pin":"..."}
POST /api/operator/logout
GET  /api/operator/session
```

Cookie name:

```text
biovolt_operator_session
```

- [ ] **Step 1: Write login-success cookie test**
- [ ] **Step 2: Write wrong-PIN generic 401 test**
- [ ] **Step 3: Write logout revocation test**
- [ ] **Step 4: Implement `require_operator_session` dependency**
- [ ] **Step 5: Apply dependency to all Phase 4 state-changing experiment/control routes**
- [ ] **Step 6: Run API/security tests and commit**

```bash
pytest tests/security tests/api/test_operator.py tests/api/test_experiments.py -v
git add src/biovolt_backend/api/operator.py src/biovolt_backend/security src/biovolt_backend/main.py tests/api/test_operator.py
git commit -m "feat: protect BioVolt operator write actions"
```

---

### Task 4: Add PWA operator session store and login dialog

**Files:**
- Create: `frontend/src/types/operator.ts`
- Create: `frontend/src/lib/operatorApi.ts`
- Create: `frontend/src/stores/operatorStore.ts`
- Create: `frontend/src/components/operator/OperatorLoginDialog.tsx`
- Create: `frontend/tests/operator/operatorStore.test.ts`
- Create: `frontend/tests/operator/OperatorLoginDialog.test.tsx`

**Interfaces:**

```ts
export type OperatorSession = {
  authenticated: boolean
  expiresAt: string | null
}
```

Use `credentials: 'include'`. Never copy cookie/session token into JavaScript state.

- [ ] **Step 1: Write session-status store test**
- [ ] **Step 2: Write PIN field/login failure/success UI tests**
- [ ] **Step 3: Implement API client and store**
- [ ] **Step 4: Clear PIN field immediately after submit**
- [ ] **Step 5: Run and commit**

```bash
cd frontend
npm test -- operator
npm run typecheck
git add src/types/operator.ts src/lib/operatorApi.ts src/stores/operatorStore.ts src/components/operator tests/operator
git commit -m "feat: add BioVolt operator login workflow"
```

---

### Task 5: Add experiment routes and setup workflow

**Files:**
- Create: `frontend/src/types/experiments.ts`
- Create: `frontend/src/lib/experimentsApi.ts`
- Create: `frontend/src/pages/ExperimentsPage.tsx`
- Create: `frontend/src/pages/ExperimentDetailPage.tsx`
- Create: `frontend/src/components/experiments/ExperimentForm.tsx`
- Create: `frontend/src/components/experiments/ExperimentStateBadge.tsx`
- Modify: `frontend/src/app/router.tsx`
- Test: `frontend/tests/experiments/ExperimentForm.test.tsx`
- Test: `frontend/tests/experiments/ExperimentDetailPage.test.tsx`

Routes:

```text
/experiments
/experiments/:experimentId
```

Create form fields:
- name
- description optional
- one or more arms
- device/cell
- mode `passive` or `manual`
- initial LED PWM
- initial mixer state only when allowed

- [ ] **Step 1: Write form validation tests**
- [ ] **Step 2: Implement create/edit draft UI**
- [ ] **Step 3: Add Ready action requiring operator session**
- [ ] **Step 4: Add start confirmation that displays device freshness, arm mode, and setpoints**
- [ ] **Step 5: On start, render `starting` and command progress rather than `running` until backend says running**
- [ ] **Step 6: Run and commit**

```bash
npm test -- experiments
npm run typecheck
git add src/pages/ExperimentsPage.tsx src/pages/ExperimentDetailPage.tsx src/components/experiments src/types/experiments.ts src/lib/experimentsApi.ts src/app/router.tsx tests/experiments
git commit -m "feat: add BioVolt experiment setup and lifecycle UI"
```

---

### Task 6: Add Manual control page with confirmed-state UX

**Files:**
- Create: `frontend/src/pages/ControlPage.tsx`
- Create: `frontend/src/lib/controlApi.ts`
- Create: `frontend/src/components/control/LedPwmControl.tsx`
- Create: `frontend/src/components/control/MixerControl.tsx`
- Create: `frontend/src/components/control/CommandStatus.tsx`
- Modify: `frontend/src/app/router.tsx`
- Test: `frontend/tests/control/ControlPage.test.tsx`

Route:

```text
/control
```

Product-state model:

```text
confirmed device state
operator edits desired value
send command
pending indicator
terminal ack
update confirmed state only from telemetry/applied ack
```

- [ ] **Step 1: Write test that clicking LED apply shows pending, not success**
- [ ] **Step 2: Write applied/rejected/expired rendering tests**
- [ ] **Step 3: Write stale-device disables control test**
- [ ] **Step 4: Implement PWM control with explicit Apply button, not continuous network writes while dragging**
- [ ] **Step 5: Implement mixer control with clear cooldown/safety rejection copy**
- [ ] **Step 6: Add Safe Stop primary emergency action that sends `safe_stop`**
- [ ] **Step 7: Run and commit**

```bash
npm test -- control
npm run typecheck
git add src/pages/ControlPage.tsx src/lib/controlApi.ts src/components/control src/app/router.tsx tests/control
git commit -m "feat: add acknowledged BioVolt manual control UI"
```

---

### Task 7: Add offline/write-safety behavior

**Files:**
- Modify: `frontend/src/pages/ControlPage.tsx`
- Modify: `frontend/src/pages/ExperimentDetailPage.tsx`
- Test: `frontend/tests/control/offlineWrites.test.tsx`

Rules:
- browser offline -> controls disabled
- backend disconnected -> controls disabled
- device stale -> actuator controls disabled
- no command is placed in Dexie for delayed later execution
- cached experiment/command history remains read-only

- [ ] **Step 1: Write offline write-disable test**
- [ ] **Step 2: Write no IndexedDB command-queue test**
- [ ] **Step 3: Implement explicit reason text for disabled actions**
- [ ] **Step 4: Run full frontend tests and commit**

```bash
npm test
npm run typecheck
npm run lint
git add src/pages/ControlPage.tsx src/pages/ExperimentDetailPage.tsx tests/control/offlineWrites.test.tsx
git commit -m "fix: prevent stale BioVolt operator commands from offline UI"
```

## Module 4.5 Exit Criteria

- [ ] PIN plaintext never persists client-side or server-side.
- [ ] Session token is inaccessible to frontend JavaScript.
- [ ] Write APIs require operator session.
- [ ] Start confirmation exposes exact arm/mode/setpoint intent.
- [ ] UI never reports actuator success before ack.
- [ ] Manual controls disable on stale/disconnected/offline conditions.
- [ ] Offline PWA does not queue hardware commands.
- [ ] Safe Stop remains clearly accessible to authenticated operator.
