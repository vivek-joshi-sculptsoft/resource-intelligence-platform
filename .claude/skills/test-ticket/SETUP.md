# Test Ticket — Setup Guide

Fetches Jira ticket(s) or an entire sprint, reads acceptance criteria, then runs targeted validation — existing tests, new test generation, API smoke tests, and AC verification. Works for backend (pytest) and frontend (vitest).

---

## Install

### Claude Code

```bash
cp -r test-ticket/ ~/.claude/skills/
```

### Claude.ai Project

1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload `references/testing-checklist.md` as knowledge

---

## Jira MCP Setup (Required)

This skill requires the Atlassian MCP for Jira integration:

```bash
claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
```

### Required Permissions

Your Jira account needs:
- **Browse projects** — to read ticket details and acceptance criteria
- **Transition issues** — to move tickets to Done after verification (optional)

---

## Trigger Phrases

The skill activates on any of these (or similar):

- "test PROJ-123"
- "validate PROJ-123"
- "verify PROJ-123"
- "QA PROJ-123"
- "check ticket PROJ-123"
- "test sprint 1"
- "validate sprint 2"
- "test PROJ-19, PROJ-20, PROJ-21"
- "test and validate all Sprint 1 tickets"

---

## Usage Examples

### Single ticket (backend)

```
"test VRIP-19"
```
-> Fetches VRIP-19 from Jira -> reads AC -> finds `tests/test_auth/test_auth_api.py` -> runs tests -> smoke tests API -> reports per-AC results

### Single ticket (frontend)

```
"validate VRIP-24"
```
-> Fetches VRIP-24 -> reads AC + mockup path -> finds/generates component tests -> checks mockup alignment -> reports

### Full sprint

```
"test sprint 1"
```
-> Queries Jira for all Sprint 1 tickets -> presents list -> you confirm -> tests each ticket -> consolidated report

### Subset of sprint

```
"test sprint 1, just the backend tickets"
```
-> Filters to backend-only tickets -> tests those

---

## How It Works

```
Step 0: Identify tickets (from keys or sprint query)
   |
Step 1: Fetch ticket details + acceptance criteria from Jira
   |  -> classify: Backend / Frontend / Both
   |  -> present test plan
   |  <- GATE: user confirmation
   |
Step 2: Discover existing tests in codebase
   |
Step 3: Run existing tests
   |
Step 4: Gap analysis -> generate tests for uncovered AC
   |
Step 5: API smoke tests (backend, if server running)
   |
Step 6: UI verification (frontend, mockup comparison)
   |
Step 7: Final report (per-AC pass/fail/gap)
   |
Step 8: Offer ticket transition to Done (if all pass)
```

---

## Prerequisites

For full test coverage, have the dev servers running:

```bash
# Backend (for API smoke tests)
/dev-backend

# Frontend (for visual verification)
/dev-frontend
```

Tests (pytest/vitest) run without dev servers. Only smoke tests and visual verification need them.

---

## File Inventory

| File | Purpose |
|---|---|
| `SKILL.md` | Core skill instructions for Claude Code |
| `claude-ai-project-prompt.md` | Condensed system prompt for Claude.ai |
| `SETUP.md` | This file — installation and usage guide |
| `references/testing-checklist.md` | Runtime checklist read at every invocation |
