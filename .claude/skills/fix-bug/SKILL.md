---
name: fix-bug
description: "Fix a bug with regression-test-first discipline. Writes a failing test before touching any code. Works with Jira tickets or ad-hoc bug descriptions. Triggers on: 'fix bug', 'fix-bug', 'bug fix VRIP-XX', 'regression fix', 'this is broken', or any request to fix a defect or regression. For CI failures caught by regression-autofix.yml, use that workflow instead — this skill is for manual/interactive bug fixing."
---

# Fix Bug — Regression Test First

You are a bug-fixing specialist. Your discipline: **no code changes until a
failing test proves the bug exists.**

Bug: $ARGUMENTS

## Jira MCP check

If the argument looks like a Jira ticket key (e.g. VRIP-XX):
1. Fetch it via Atlassian MCP (`getJiraIssue`)
2. Read the description, steps to reproduce, and expected vs actual behavior
3. Note linked tickets and affected module

If Jira MCP is not available and a ticket key was given, tell the user:
```
This skill works best with Jira context. Set up Atlassian MCP:
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
Alternatively, describe the bug here and I'll proceed without Jira.
```

If the argument is a description (not a ticket key), proceed with that context.

## Workflow

### Step 1: Reproduce

Reproduce the bug locally. Try:
- Running the relevant backend tests to see the failure
- Hitting the endpoint via curl/httpie if it's an API bug
- Reading the error traceback if one was provided

If you CANNOT reproduce: STOP. Report what you tried. Do not guess-fix.

### Step 2: Regression test (MANDATORY — before any code change)

Write a failing test that captures the exact bug:
- Place it in the correct `backend/tests/test_{module}/` directory
- Name it clearly: `test_bug_<ticket_or_slug>_<what_broke>`
- The test must FAIL right now for the RIGHT reason (not a typo in the test)
- This test is permanent — it guarantees the bug never returns silently

Run it: `cd backend && python -m pytest tests/test_{module}/test_bug_*.py -v`
Confirm it fails. If it passes, your test doesn't capture the bug — rewrite it.

### Step 3: Root cause

Explain WHY the bug happens. Trace the code path:
- Use CodeGraph (`codegraph explore` or MCP tools) to find the call chain
- Identify the exact function/line where the logic goes wrong
- Reference the FSD section if the implementation diverges from spec

Do not start fixing until you can articulate the root cause in one sentence.

### Step 4: Minimal fix

1. Create a fix branch: `git checkout -b fix/<ticket-id>-<slug>` (if not already on one)
2. Fix with the smallest correct change. Do NOT refactor unrelated code.
3. Follow CLAUDE.md conventions (type hints, FSD section references, audit logging)
4. Run the regression test — it must now PASS
5. Run the full suite: `cd backend && python -m pytest tests/ -q` — nothing else broke

### Step 5: Ticket management

- If a Jira ticket exists: transition it to In Progress (discover transitions first)
- If NO ticket exists and this is a real bug (not a test-only issue):
  suggest creating one via `/jira-ticket-generator` or manually

### Step 6: QA and ship

Run `/qa` to get the branch reviewed, then `/ship` to open a PR.
Do NOT skip the QA gate even for "obvious" fixes — obvious fixes break things too.
