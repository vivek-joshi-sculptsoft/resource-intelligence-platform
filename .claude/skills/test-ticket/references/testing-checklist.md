# Test Ticket — Runtime Testing Checklist

Read this at the start of every invocation. Use it as a live checklist to ensure no step is skipped.

---

## Pre-Flight

- [ ] Check for Jira MCP tools (tool names containing `atlassian` or `jira`)
  - If not available -> tell user to set up Atlassian MCP, STOP
- [ ] Discover cloudId — call `getAccessibleAtlassianResources` or use cached/known value
  - One site -> use it
  - Multiple sites -> ask user

---

## Step 0: Identify Tickets

- [ ] Extract ticket keys from user message (pattern: `{PROJECT}-{NUMBER}`)
- [ ] Or detect sprint-level command (`test sprint N`, `validate sprint N`)
  - Query Jira for sprint tickets via JQL
  - Present ticket list for confirmation
- [ ] If no keys or sprint found -> ask user for ticket key(s)

---

## Step 1: Fetch Ticket Details & AC

For each ticket key:
- [ ] Call `getJiraIssue` with `responseContentFormat: "markdown"`
- [ ] Extract: key, summary, type, status, full description
- [ ] Parse acceptance criteria (checkbox lists, numbered lists, AC section)
- [ ] Extract context: mockup paths, module references, spec files
- [ ] Classify scope: Backend / Frontend / Both
- [ ] Present test plan with AC per ticket
- [ ] **WAIT FOR USER CONFIRMATION**

---

## Step 2: Discover Existing Tests

- [ ] Backend: search `backend/tests/` for related test files
- [ ] Frontend: search `frontend/src/` for `.test.*` / `.spec.*` files
- [ ] Report what exists per ticket

---

## Step 3: Run Existing Tests

- [ ] Backend: `python3 -m pytest {files} -v --tb=short`
- [ ] Frontend: `npx vitest run {files} --reporter=verbose`
- [ ] If no specific files, run full suite for regression check
- [ ] Report pass/fail counts per ticket

---

## Step 4: Gap Analysis & Test Generation

For each AC item:
- [ ] Mark as: Covered / Partially covered / Not covered
- [ ] Generate new tests for uncovered AC items
- [ ] Follow existing test patterns (read conftest.py, existing tests)
- [ ] Backend: pytest + AsyncClient, place in `tests/test_{module}/`
- [ ] Frontend: vitest + @testing-library/react, match existing placement
- [ ] Run new tests and report results
- [ ] **Only test what AC specifies — no over-testing**

---

## Step 5: API Smoke Tests (Backend Only)

- [ ] Check if backend server running on :8000
  - Not running -> skip, suggest `/dev-backend`
- [ ] For each API endpoint in AC:
  - [ ] Test with valid input (happy path)
  - [ ] Test with invalid input (error case)
  - [ ] Test access control (unauthenticated, wrong role)
- [ ] Login first for protected endpoints (get cookies)
- [ ] Report per-endpoint results

---

## Step 6: UI Verification (Frontend Only)

- [ ] Read mockup HTML from ticket context
- [ ] Read implemented component source
- [ ] Check structural alignment:
  - [ ] Theme colors (navy primary, orange-red accent)
  - [ ] Layout structure (cards, spacing, grid)
  - [ ] Required elements (icons, badges, buttons, empty states)
  - [ ] Interactive behaviors (dropdowns, toggles, filters)
- [ ] Report matches and mismatches
- [ ] Check if frontend server running on :5173 for visual verification

---

## Step 7: Final Report

- [ ] Map every AC item to test result (Pass / Fail / Gap)
- [ ] Per-ticket status: PASS / PARTIAL / FAIL
- [ ] Summary table: tickets x AC items x results
- [ ] List action items for any gaps or failures

---

## Step 8: Offer Ticket Transition

- [ ] All AC passed -> offer to transition to "Done"
  - Discover transitions via `getTransitionsForJiraIssue`
- [ ] Gaps or failures exist -> do NOT offer transition, list what needs fixing

---

## Quick Reference

| Check | Backend | Frontend |
|-------|---------|----------|
| Test runner | `python3 -m pytest` | `npx vitest run` |
| Test location | `backend/tests/test_{module}/` | alongside component or `__tests__/` |
| Server port | 8000 | 5173 |
| Start command | `/dev-backend` | `/dev-frontend` |
| Smoke test tool | `curl` | browser (manual) |
