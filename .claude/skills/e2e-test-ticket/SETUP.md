# E2E Test Ticket — Setup Guide

Generates Playwright E2E test specs from Jira tickets. Each spec file maps 1:1 to a ticket, organized by sprint. Smoke-tagged tests run in CI on every push.

---

## Install

### 1. Install Playwright

```bash
cd e2e && npm install && npx playwright install chromium
```

### 2. Verify Setup

```bash
cd e2e && npx playwright test --list
```

Should show global setup tests.

### 3. Claude Code Skill

Already installed at `.claude/skills/e2e-test-ticket/`. No extra setup needed.

---

## Jira MCP Setup (Required)

```bash
claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
```

---

## Trigger Phrases

- "e2e VRIP-31"
- "e2e test VRIP-31"
- "playwright VRIP-31"
- "generate e2e for VRIP-31"
- "e2e sprint 2"
- "playwright tests for sprint 2"
- "e2e VRIP-31, VRIP-35, VRIP-40"

---

## Running Tests

```bash
# All E2E tests
cd e2e && npx playwright test

# Smoke tests only (runs in CI)
cd e2e && npx playwright test --grep @smoke

# Specific sprint
cd e2e && npx playwright test tests/sprint-2/

# Specific ticket
cd e2e && npx playwright test tests/sprint-2/VRIP-31*

# Interactive UI mode
cd e2e && npx playwright test --ui

# Generate test code via recording
cd e2e && npx playwright codegen http://localhost:5173
```

---

## CI Integration

Smoke tests run automatically on every push and PR via `.github/workflows/e2e-smoke.yml`.

- Runs only `@smoke` tagged tests (fast — under 2 minutes)
- Uses Chromium only
- Uploads failure screenshots and traces as artifacts
- Does NOT block the build on failure (configured as a separate check)

Full E2E suite can be triggered manually from the Actions tab.

---

## File Structure

```
e2e/
├── package.json              # Playwright dependency
├── playwright.config.ts      # Config: webServer, projects, reporter
├── global.setup.ts           # Verify backend + frontend health
├── tsconfig.json
├── fixtures/
│   ├── auth.ts               # loginAs(role) fixture for all 7 roles
│   └── index.ts              # Re-exports
├── utils/
│   ├── api.ts                # Direct API helpers for test setup/teardown
│   └── constants.ts          # Route paths, timeouts
└── tests/
    ├── sprint-1/
    │   └── VRIP-XX-slug.spec.ts
    ├── sprint-2/
    │   └── VRIP-XX-slug.spec.ts
    └── ...
```

---

## How It Works

```
User: "e2e VRIP-31"
  ↓
Step 0: Extract ticket key
Step 1: Fetch from Jira → parse AC → read SCREENS.md + mockup + component source
  ↓ (user confirms test plan)
Step 2: Generate e2e/tests/sprint-2/VRIP-31-resource-crud.spec.ts
Step 3: Run tests → report pass/fail per AC
Step 4: Verify smoke tag coverage
Step 5: Final report with run commands
```
