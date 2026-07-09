# Design: `backend-test-ticket` skill

**Date:** 2026-07-06
**Status:** Approved (design), pending implementation plan

## Summary

A Jira-ticket-driven, backend-**pytest** test-maintenance skill. Given a ticket, it
determines which pytest files must be **created** vs **updated** to cover the code that
ticket changed, presents that plan for approval, then (on approval) writes the tests, runs
them, self-heals broken *tests* (never feature code), and reports.

It is **standalone**. Overlap with the existing `test-ticket` skill is accepted by choice —
the user selects which skill to invoke per task.

## Goals

- Keep the backend pytest suite in sync with code delivered under a ticket.
- Distinguish **CREATE** (no test exists) from **UPDATE** (test exists but behavior changed)
  from **NO-OP** (pure refactor, existing tests still valid).
- Be **fully generic / portable**: assume only "Python + pytest", auto-detect everything
  else (web framework, ORM, async vs sync, test layout, fixtures, runner command) by
  reading the target repo. No project-specific rules baked in.
- Never modify feature code. Only test files and test fixtures.

## Non-Goals

- Frontend (vitest) or E2E (Playwright) tests — covered by `e2e-test-ticket` / `test-ticket`.
- Broad AC-by-AC QA validation — that is `test-ticket`'s job.
- Fixing product bugs. If a genuine product bug is found, it is **reported, not fixed**.
- Language-agnostic support (Node/Go/etc.). Python + pytest only.

## Boundary vs Existing Skills

| Skill | Domain | Driver | Emphasis |
|---|---|---|---|
| `test-ticket` | backend + frontend | Jira AC | broad multi-layer validation, per-AC pass/fail |
| `e2e-test-ticket` | E2E (Playwright) | Jira ticket | end-to-end flows across tiers |
| **`backend-test-ticket`** | **backend pytest only** | **Jira ticket + git diff** | **surgical create/update of unit/integration tests for the code delta** |

## Trigger

Phrases such as `backend tests for VRIP-52`, `sync backend tests VRIP-52`,
`pytest for PROJ-123`, `backend-test-ticket PROJ-123`.

**Jira MCP required.** At startup, check for tools containing `atlassian` or `jira`. If
absent, print the setup hint (`claude mcp add --transport http --scope user atlassian
https://mcp.atlassian.com/v1/mcp`) and stop — same guard pattern as `test-ticket`.

## Workflow

1. **Fetch ticket** — `getJiraIssue` with the key. Read description + acceptance criteria.
   Extract any module/file/endpoint references.

2. **Locate changed code** (primary: git; fallback: ticket refs):
   1. Find the ticket's branch or commits (branch name or commit message containing the
      ticket key) and `git diff` vs `main` to get the exact changed source files/symbols.
   2. If no branch/commits found: parse the ticket description for module/file references
      and grep the repo to confirm targets.
   3. Produce a concrete list of changed backend source files and symbols. Exclude test
      files, migrations, and docs from the "code under test" list.

3. **Auto-detect the test setup** (portability layer) — read the repo, do not assume:
   - Test directory layout and naming (`tests/`, `test_*.py`, mirror-of-source, etc.).
   - `conftest.py` fixtures — especially client, db/session, and auth/login helpers.
   - Runner command and config (`pyproject.toml [tool.pytest.ini_options]`, `pytest.ini`,
     `setup.cfg`), markers, coverage config.
   - Web framework (FastAPI/Flask/Django), ORM, and async vs sync test style.

4. **Map code → tests** — for each changed source file, find its existing test file(s) and
   classify each affected symbol:
   - **CREATE** — no test covers this symbol.
   - **UPDATE** — a test exists but the change alters signature/return shape, adds a new
     branch/param/error path, or invalidates an existing assertion.
   - **NO-OP** — pure refactor; existing tests remain valid.

5. **Present the plan & gate (APPROVAL REQUIRED)** — output a table:
   `source symbol → test file → CREATE | UPDATE | NO-OP → reason`.
   **Wait for explicit user approval before writing anything.** Nothing is written blind.

6. **Write tests** — on approval, follow the detected fixtures/conventions. Cover the happy
   path plus the change's new branches and edge/error paths. For UPDATEs, add/adjust cases
   for the changed behavior rather than rewriting the whole file. Match the surrounding
   test style (fixture usage, naming, assertion idiom).

7. **Run & self-heal** — run the affected tests. If a *test* is wrong (bad fixture, stale
   expectation), fix the test and re-run. Never edit feature code. Loop until green or a
   real product bug is isolated.

8. **Report** — per-file CREATE/UPDATE/NO-OP summary, final pass/fail with the run command
   used, coverage delta if available, and any suspected product bugs surfaced (described,
   not fixed).

## Create-vs-Update Heuristics (the "identify" core)

- **CREATE** when the changed source symbol has no corresponding test.
- **UPDATE** when a test exists but at least one holds:
  - function/endpoint signature or return/response shape changed;
  - a new parameter, branch, or error path was introduced;
  - an existing assertion now contradicts the new behavior
    (example: an auth-cookie `secure` flag becoming environment-dependent → add a
    regression case pinning the new behavior to the existing auth test).
- **NO-OP** when the diff is a pure refactor with no behavioral change — report
  "no test change needed" as a valid, first-class outcome.

## Files & Location

```
backend-test-ticket/
├── SKILL.md          # generic workflow (this design)
└── references/
    └── heuristics.md # create/update rules, detection recipes, self-heal policy,
                      # examples of good CREATE vs UPDATE calls
```

Authored in the **`agentic-sdlc-skills-agents` submodule** and added to its `install.sh`
SKILLS list, so it is portable and version-controlled across projects, then installed into
each project's `.claude/skills/` like the rest of the family.

## Safety / Constraints

- **Approval gate** before any write (step 5). Non-negotiable per user decision.
- **Never modify feature code** — test files and fixtures only.
- **Report, don't hide, product bugs.**
- **No project-specific rules** in `SKILL.md`; everything project-shaped is detected at run
  time from the target repo.

## Open Questions

- None blocking. (Sprint-level batch mode — "sync backend tests for a whole sprint" — is a
  possible future extension, deliberately out of scope for v1.)
