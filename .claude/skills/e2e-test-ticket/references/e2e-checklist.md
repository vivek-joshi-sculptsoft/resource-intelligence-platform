# E2E Test Ticket — Runtime Checklist (3-Tier)

Read this at the start of every invocation. Use as a live checklist.

---

## Pre-Flight

- [ ] Check for Jira MCP tools (`atlassian` or `jira` in tool names)
  - Not available → tell user to set up Atlassian MCP, STOP
- [ ] Discover cloudId — `getAccessibleAtlassianResources` or use known value
- [ ] Verify Playwright is installed: `cd e2e && npx playwright --version`

---

## Step 0: Identify Tickets

- [ ] Extract ticket keys from user message (`{PROJECT}-{NUMBER}`)
- [ ] Or detect sprint-level command (`e2e sprint N`)
- [ ] No tickets found → ask user

---

## Step 1: Fetch Ticket Details & Context

For each ticket:
- [ ] `getJiraIssue` with `responseContentFormat: "markdown"`
- [ ] Extract: key, summary, type, status, sprint
- [ ] Parse acceptance criteria into numbered list
- [ ] Read module's `SCREENS.md`, `API.md`, mockup HTML
- [ ] Read actual frontend component — real selectors
- [ ] Read `e2e/fixtures/auth.ts`
- [ ] Check for existing spec
- [ ] Present test plan for all 3 tiers
- [ ] **WAIT FOR USER CONFIRMATION**

---

## Step 2: Generate Tier 1 — Ticket Tests

- [ ] Dir: `e2e/tests/tickets/sprint-N/`
- [ ] File: `{STORY-ID}-{slug}.spec.ts`
- [ ] Import from `../../../fixtures`
- [ ] One `test.describe` per ticket
- [ ] One `test()` per AC item
- [ ] Include access control tests
- [ ] Use `loginAs(role)`, real selectors, `waitForResponse`

---

## Step 3: Generate Tier 2 — Integration Tests

- [ ] Dir: `e2e/tests/integration/`
- [ ] File: `{module}-flow.spec.ts`
- [ ] Import from `../../fixtures`
- [ ] Full lifecycle tests (create → view → edit → deactivate)
- [ ] Cross-role tests (HR creates, PM views)
- [ ] Cross-module tests (resource appears in project dropdown, etc.)

---

## Step 4: Generate Tier 3 — Smoke Tests

- [ ] Dir: `e2e/tests/smoke/`
- [ ] File: `{module}-smoke.spec.ts`
- [ ] Import from `../../fixtures`
- [ ] One happy-path test per core feature
- [ ] Each test < 10 seconds
- [ ] No edge cases, no error paths

---

## Step 5: Run Tests

- [ ] `cd e2e && npx playwright test --project=tickets --reporter=list`
- [ ] `cd e2e && npx playwright test --project=integration --reporter=list`
- [ ] `cd e2e && npx playwright test --project=smoke --reporter=list`

---

## Step 6: Final Report

- [ ] Table per tier: file | tests | pass | fail
- [ ] Summary: total tests, total pass, total fail per tier
- [ ] Failure details
- [ ] Run commands

---

## Quick Reference

| Action | Command |
|--------|---------|
| All tiers | `cd e2e && npx playwright test` |
| Smoke only | `cd e2e && npx playwright test --project=smoke` |
| Tickets only | `cd e2e && npx playwright test --project=tickets` |
| Integration | `cd e2e && npx playwright test --project=integration` |
| Sprint folder | `cd e2e && npx playwright test tests/tickets/sprint-N/` |
| Single ticket | `cd e2e && npx playwright test tests/tickets/sprint-N/S2-05*` |
| UI mode | `cd e2e && npx playwright test --ui` |
| List tests | `cd e2e && npx playwright test --list` |
| Report | `cd e2e && npx playwright show-report` |
