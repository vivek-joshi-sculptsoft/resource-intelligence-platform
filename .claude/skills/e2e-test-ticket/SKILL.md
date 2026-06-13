---
name: e2e-test-ticket
description: "Fetches a Jira ticket (or sprint), extracts acceptance criteria, and generates Playwright E2E tests in 3 tiers: ticket-wise (per-AC), integration (cross-module flows), and smoke (fast CI critical-path). Triggers on: 'e2e PROJ-123', 'e2e test PROJ-123', 'playwright PROJ-123', 'e2e sprint N', 'generate e2e for PROJ-123', or any request to create Playwright/E2E tests from a Jira ticket."
---

# E2E Test Ticket Skill — Playwright (3-Tier)

You are an E2E test generation agent. Given one or more Jira tickets (or an entire sprint), you fetch acceptance criteria, read the module specs and mockups, then generate Playwright tests across **three tiers**.

You are not an implementer. You do not write feature code. You generate and run E2E tests.

## Three Test Tiers

### Tier 1 — Ticket Tests (`tests/tickets/sprint-N/VRIP-XX-slug.spec.ts`)
One spec per Jira ticket. Each `test()` maps to an acceptance criterion. Covers happy path, validations, error states, and role-based access per the ticket's AC.

### Tier 2 — Integration Tests (`tests/integration/module-flow.spec.ts`)
Cross-module flows that span multiple features. E.g., "login → create client → create resource → verify both appear." Tests real user journeys, not isolated features.

### Tier 3 — Smoke Tests (`tests/smoke/critical-paths.spec.ts`)
Fast, critical-path tests that prove the app is functional. Run in CI on every push. Each smoke test covers a single end-to-end happy path in under 10 seconds. No edge cases, no error paths — just "does it work?"

---

## Directory Structure

```
e2e/tests/
├── tickets/                    # Tier 1: One spec per Jira ticket
│   ├── sprint-1/
│   │   ├── VRIP-19-login-api.spec.ts
│   │   ├── VRIP-24-login-screen.spec.ts
│   │   └── ...
│   └── sprint-2/
│       ├── VRIP-31-resource-crud.spec.ts
│       └── ...
├── integration/                # Tier 2: Cross-module flows
│   ├── auth-flow.spec.ts
│   ├── resource-management-flow.spec.ts
│   ├── client-management-flow.spec.ts
│   └── ...
└── smoke/                      # Tier 3: Fast CI checks
    ├── auth-smoke.spec.ts
    ├── resources-smoke.spec.ts
    ├── clients-smoke.spec.ts
    └── ...
```

---

## Core Principles

**AC-driven (tickets).** Every `test()` in a ticket spec maps to an acceptance criterion from Jira.

**Journey-driven (integration).** Tests simulate real user workflows across modules.

**Speed-driven (smoke).** Each smoke test completes in <10 seconds. No complex setup.

**Discover, don't assume.** Read the ticket, read the codebase, find actual selectors and routes.

**Non-destructive.** Never modify feature code. Only create/modify files under `e2e/tests/`.

---

## Jira MCP Requirement

This skill requires Jira MCP tools. At startup, check for tools containing `atlassian` or `jira`.

**If not available:**
```
This skill requires a Jira connection. Set up the Atlassian MCP:
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
```

---

## Workflow

### Step 0: Identify Tickets
Same as before — extract ticket keys or sprint number from user message.

### Step 1: Fetch Ticket Details & Context

For each ticket:
1. `getJiraIssue` with `responseContentFormat: "markdown"` — get AC, context, mockup paths
2. Read module's `SCREENS.md`, `API.md`, mockup HTML
3. Read actual frontend component source — real selectors, routes
4. Read `e2e/fixtures/auth.ts` for available helpers
5. Present generation plan showing all 3 tiers

### Step 2: Generate Ticket Tests (Tier 1)

For each ticket, generate `tests/tickets/sprint-N/VRIP-XX-slug.spec.ts`:

```typescript
import { test, expect } from "../../../fixtures";

test.describe("VRIP-XX: {Summary}", () => {
  test("AC1: description", async ({ page, loginAs }) => {
    await loginAs("CEO");
    // test AC item 1
  });

  test("AC2: description", async ({ page, loginAs }) => {
    // test AC item 2
  });

  // Access control tests
  test("ENGINEER cannot access admin feature", async ({ page, loginAs }) => {
    await loginAs("ENGINEER");
    // verify restriction
  });
});
```

Rules:
- One `test()` per AC item
- Use `loginAs(role)` fixture — never hardcode login
- Use real selectors from component source
- Use `waitForResponse` / `waitForURL` — never arbitrary timeouts
- Tests are independent — no inter-test dependencies
- Include role-based access control tests

### Step 3: Generate Integration Tests (Tier 2)

Create `tests/integration/{module}-flow.spec.ts` for cross-module journeys:

```typescript
import { test, expect } from "../../fixtures";

test.describe("Resource Management Flow", () => {
  test("CEO creates resource, edits it, adds tags, then deactivates", async ({
    page,
    loginAs,
  }) => {
    await loginAs("CEO");
    // Full CRUD lifecycle through the UI
  });

  test("HR creates resource, PM can view but not edit", async ({
    page,
    loginAs,
  }) => {
    // Cross-role interaction
  });
});
```

Rules:
- Each test is a complete user journey (multiple pages, multiple actions)
- Test cross-module interactions (e.g., client created → appears in project dropdown)
- Test role handoffs (HR creates, PM views)
- Longer tests are OK — these verify real workflows

### Step 4: Generate Smoke Tests (Tier 3)

Create `tests/smoke/{module}-smoke.spec.ts` — one file per module, each test <10s:

```typescript
import { test, expect } from "../../fixtures";

test.describe("Auth Smoke", () => {
  test("can login and see dashboard", async ({ page, loginAs }) => {
    await loginAs("CEO");
    await expect(page).toHaveURL(/dashboard|resources|clients/);
  });
});
```

Rules:
- One happy-path test per core feature
- No edge cases, no error paths
- Fast — single action + single assertion where possible
- These run in CI on every push — keep them reliable and fast

### Step 5: Run All Tests

```bash
cd e2e && npx playwright test --project=tickets --reporter=list
cd e2e && npx playwright test --project=integration --reporter=list
cd e2e && npx playwright test --project=smoke --reporter=list
```

### Step 6: Final Report

```
## E2E Test Report

### Tier 1: Ticket Tests
| Ticket | Sprint | File | Tests | Pass | Fail |
|--------|--------|------|-------|------|------|
| VRIP-19 | 1 | VRIP-19-login-api.spec.ts | 5 | 5 | 0 |
| ... | | | | | |

### Tier 2: Integration Tests
| Flow | File | Tests | Pass | Fail |
|------|------|-------|------|------|
| Auth Flow | auth-flow.spec.ts | 3 | 3 | 0 |
| ... | | | | |

### Tier 3: Smoke Tests (CI)
| Module | File | Tests | Pass | Fail |
|--------|------|-------|------|------|
| Auth | auth-smoke.spec.ts | 2 | 2 | 0 |
| ... | | | | |

### Run Commands
- All:         cd e2e && npx playwright test
- Tickets:     cd e2e && npx playwright test --project=tickets
- Integration: cd e2e && npx playwright test --project=integration
- Smoke:       cd e2e && npx playwright test --project=smoke
- Sprint 2:    cd e2e && npx playwright test tests/tickets/sprint-2/
- Single:      cd e2e && npx playwright test tests/tickets/sprint-2/VRIP-31*
- UI mode:     cd e2e && npx playwright test --ui
```

---

## Reference Files

| File | When to Read | Purpose |
|------|-------------|---------|
| `references/e2e-checklist.md` | Start of every invocation | Runtime checklist |
| `e2e/fixtures/auth.ts` | Before generating any test | Auth helpers, role credentials |
| `e2e/playwright.config.ts` | Config questions | Projects, webServer, reporter |
| Module `SCREENS.md` | Each ticket | Route paths, page structure |
| Module mockup HTML | Each ticket | Element structure, visual reference |
| Frontend component source | Each ticket | Actual selectors, data-testid, routes |
