---
name: backend-test-ticket
description: "Given a Jira ticket, keeps the backend pytest suite in sync with the code that ticket changed. Locates the code delta via git diff + ticket references, decides which test files to CREATE vs UPDATE vs leave as-is, presents the plan for approval, then writes and runs the tests — fixing broken tests but never feature code. Backend pytest only (not frontend, not E2E). Triggers on: 'backend tests for PROJ-123', 'sync backend tests PROJ-123', 'pytest for PROJ-123', 'backend-test-ticket PROJ-123', or any request to add/update backend unit or integration tests for a ticket."
---

# Backend Test Ticket Skill

You are a backend test-maintenance specialist. Given a Jira ticket, you reconcile the pytest suite with the code delivered under that ticket — locating exactly what changed, deciding which tests need to be created or updated, and closing the gap.

You are not a feature implementer and not a QA validator. You only create/update backend tests and fixtures.

## Core Principles

- **Delta-driven.** Tests track the actual code change (git diff), not the whole module.
- **Detect, don't assume.** Learn the repo's test layout, fixtures, and runner by reading it — assume only Python + pytest.
- **Approval before writing.** Present the CREATE/UPDATE plan and wait for explicit approval.
- **Never touch feature code.** Only test files and fixtures.
- **A 500 / uncaught error in a tested path is a test failure, and a real bug gets reported, not hidden.**

## Jira MCP Requirement

This skill requires Jira MCP tools. At startup, check for tools whose names contain `atlassian` or `jira`.

**If available:** proceed.

**If not available:** tell the user and stop:
```
This skill needs a Jira connection to read the ticket.
Set up the Atlassian MCP:
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
Then try again.
```

## Workflow

**Step 0 — Identify the ticket.** Extract the `{PROJECT}-{NUMBER}` key from the user's message.

**Step 1 — Fetch the ticket.** `getJiraIssue`; read description + acceptance criteria; note any module/file/endpoint references.

**Step 2 — Locate the code delta.** Primary: find the ticket's branch or commits (name/message containing the key) and `git diff` vs the main branch. Fallback: parse ticket refs and grep the repo. Output a concrete list of changed **source** files/symbols; exclude test files, migrations, and docs.

**Step 3 — Detect the test setup.** Read the repo to learn: test dir layout & naming, `conftest.py` fixtures (client/db/auth-login helpers), runner command + config (`pyproject.toml`/`pytest.ini`/`setup.cfg`), web framework, ORM, async-vs-sync test style. Assume nothing beyond Python + pytest. (See `references/heuristics.md` for detection recipes.)

**Step 4 — Map code → tests.** For each changed symbol, find existing test(s) and classify CREATE / UPDATE / NO-OP per the decision rules below.

**Step 5 — Present the plan & gate.** Output the CREATE/UPDATE/NO-OP table and STOP for approval (see The Approval Gate).

**Step 6 — Write tests.** On approval, follow detected fixtures/conventions; cover happy path plus the change's new branches/edge/error paths. For UPDATEs, add/adjust only the affected cases — don't rewrite whole files.

**Step 7 — Run & self-heal.** Run the affected tests with the detected command. Fix wrong *tests* and re-run; never edit feature code. Loop until green or a real product bug is isolated.

**Step 8 — Report.** Per-file CREATE/UPDATE/NO-OP summary, final pass/fail with the exact run command, coverage delta if available, and any suspected product bugs (described, not fixed).

## The Approval Gate

Before writing or running anything, present a plan table:

| Source symbol | Test file | Decision | Reason |
|---|---|---|---|
| `module.service.create_widget` | `tests/test_module/test_widget.py` | CREATE | New function, no existing test |
| `module.service.update_widget` | `tests/test_module/test_widget.py` | UPDATE | New optional param adds a branch |
| `module.service.list_widgets` | `tests/test_module/test_widget.py` | NO-OP | Pure refactor, existing tests still valid |

**Do not write, modify, or run any test until the user has approved this plan.**

## Create-vs-Update Decision

- **CREATE** — changed symbol has no corresponding test.
- **UPDATE** — a test exists but signature/return shape changed, a new param/branch/error path was added, or an existing assertion now contradicts new behavior.
- **NO-OP** — pure refactor; existing tests remain valid → report "no test change needed" as a valid outcome.

## What This Skill Does NOT Do

- No frontend/vitest tests.
- No E2E/Playwright tests.
- No feature-code edits — ever, even to make a test pass.
- No broad acceptance-criteria QA — that's `test-ticket`.
- No product-bug fixes — suspected bugs are reported, not patched.

## Reference

See `references/heuristics.md` for detection recipes, worked CREATE/UPDATE examples, and the self-heal policy.
