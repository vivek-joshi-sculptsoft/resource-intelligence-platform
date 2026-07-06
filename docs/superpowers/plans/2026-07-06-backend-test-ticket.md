# backend-test-ticket Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author a portable, Jira-ticket-driven `backend-test-ticket` skill that identifies which pytest files must be CREATED vs UPDATED for a ticket's code delta, gates on user approval, then writes and runs the tests.

**Architecture:** The skill is a prose artifact (`SKILL.md` + `references/heuristics.md`) authored in the `agentic-sdlc-skills-agents` git submodule (the portable source of truth), registered in that submodule's `install.sh`, then installed into this project's `.claude/skills/`. No project-specific rules live in `SKILL.md`; everything project-shaped is auto-detected at run time.

**Tech Stack:** Markdown skill files (Claude Code skill format: YAML frontmatter + body). Bash `install.sh`. Git submodule. Validation is manual/dry-run, not pytest — this deliverable ships no runtime code.

## Global Constraints

- Skill frontmatter is exactly two keys: `name` and `description` (quoted). Match the house style of `submodules/agentic-sdlc-skills-agents/skills/implement-ticket/SKILL.md`.
- `SKILL.md` must contain **no project-specific rules** (no `app/modules/*`, no RolePermission/AuditLog/FSD references as requirements). Project specifics are auto-detected from the target repo at run time. RIP-flavored items may appear only as clearly-labeled *illustrative examples*.
- Domain is **backend pytest only**. Never frontend, never E2E, never feature code.
- **Approval gate is mandatory** before any file write (workflow step 5).
- Jira MCP is **required**; absent → print setup hint and stop.
- Files authored under `submodules/agentic-sdlc-skills-agents/` are committed to the **submodule repo**; the copy under `.claude/skills/` is committed to the **superproject** branch `skill/backend-test-ticket`.
- Skill directory name: `backend-test-ticket`.

---

## File Structure

- `submodules/agentic-sdlc-skills-agents/skills/backend-test-ticket/SKILL.md` — generic workflow (source of truth).
- `submodules/agentic-sdlc-skills-agents/skills/backend-test-ticket/references/heuristics.md` — create/update rules, detection recipes, self-heal policy, worked examples.
- `submodules/agentic-sdlc-skills-agents/install.sh` — add `backend-test-ticket` to the `SKILLS` array.
- `.claude/skills/backend-test-ticket/` — installed copy for this project (SKILL.md + references/).

---

## Task 1: Author `SKILL.md` in the submodule

**Files:**
- Create: `submodules/agentic-sdlc-skills-agents/skills/backend-test-ticket/SKILL.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the skill's canonical workflow. Task 3 references `references/heuristics.md` from it; Task 4 registers the directory name `backend-test-ticket`; Task 5 copies this file.

- [ ] **Step 1: Define the acceptance check for this file (what "done" means)**

The finished `SKILL.md` must satisfy all of:
1. Frontmatter has exactly `name: backend-test-ticket` and a quoted `description` containing trigger phrases.
2. Body contains these sections in order: intro paragraph, `## Core Principles`, `## Jira MCP Requirement`, `## Workflow` (steps 0–8), `## The Approval Gate`, `## Create-vs-Update Decision`, `## What This Skill Does NOT Do`, `## Reference`.
3. Contains the verbatim approval-gate sentence and the verbatim Jira-guard block below.
4. Grep proves no hardcoded project rule: `grep -nE 'app/modules|RolePermission|AuditLog|FSD §' SKILL.md` returns only lines that are inside an "example" callout (or nothing).

- [ ] **Step 2: Write the frontmatter (verbatim)**

```yaml
---
name: backend-test-ticket
description: "Given a Jira ticket, keeps the backend pytest suite in sync with the code that ticket changed. Locates the code delta via git diff + ticket references, decides which test files to CREATE vs UPDATE vs leave as-is, presents the plan for approval, then writes and runs the tests — fixing broken tests but never feature code. Backend pytest only (not frontend, not E2E). Triggers on: 'backend tests for PROJ-123', 'sync backend tests PROJ-123', 'pytest for PROJ-123', 'backend-test-ticket PROJ-123', or any request to add/update backend unit or integration tests for a ticket."
---
```

- [ ] **Step 3: Write the intro + Core Principles**

Intro (2 short paragraphs): "You are a backend test-maintenance specialist. Given a Jira ticket, you reconcile the pytest suite with the code delivered under that ticket…" and "You are not a feature implementer and not a QA validator. You only create/update backend tests and fixtures."

`## Core Principles` bullets:
- **Delta-driven.** Tests track the actual code change (git diff), not the whole module.
- **Detect, don't assume.** Learn the repo's test layout, fixtures, and runner by reading it — assume only Python + pytest.
- **Approval before writing.** Present the CREATE/UPDATE plan and wait for explicit approval.
- **Never touch feature code.** Only test files and fixtures.
- **A 500 / uncaught error in a tested path is a test failure, and a real bug gets reported, not hidden.**

- [ ] **Step 4: Write the Jira guard (verbatim)**

````markdown
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
````

- [ ] **Step 5: Write the Workflow section (steps 0–8)**

Author `## Workflow` with these steps, each 1–3 sentences, imperative voice:

- **Step 0 — Identify the ticket.** Extract the `{PROJECT}-{NUMBER}` key from the user's message.
- **Step 1 — Fetch the ticket.** `getJiraIssue`; read description + acceptance criteria; note any module/file/endpoint references.
- **Step 2 — Locate the code delta.** Primary: find the ticket's branch or commits (name/message containing the key) and `git diff` vs the main branch. Fallback: parse ticket refs and grep the repo. Output a concrete list of changed **source** files/symbols; exclude test files, migrations, and docs.
- **Step 3 — Detect the test setup.** Read the repo to learn: test dir layout & naming, `conftest.py` fixtures (client/db/auth-login helpers), runner command + config (`pyproject.toml`/`pytest.ini`/`setup.cfg`), web framework, ORM, async-vs-sync test style. Assume nothing beyond Python + pytest. (See `references/heuristics.md` for detection recipes.)
- **Step 4 — Map code → tests.** For each changed symbol, find existing test(s) and classify CREATE / UPDATE / NO-OP per the decision rules below.
- **Step 5 — Present the plan & gate.** Output the CREATE/UPDATE/NO-OP table and STOP for approval (see The Approval Gate).
- **Step 6 — Write tests.** On approval, follow detected fixtures/conventions; cover happy path plus the change's new branches/edge/error paths. For UPDATEs, add/adjust only the affected cases — don't rewrite whole files.
- **Step 7 — Run & self-heal.** Run the affected tests with the detected command. Fix wrong *tests* and re-run; never edit feature code. Loop until green or a real product bug is isolated.
- **Step 8 — Report.** Per-file CREATE/UPDATE/NO-OP summary, final pass/fail with the exact run command, coverage delta if available, and any suspected product bugs (described, not fixed).

- [ ] **Step 6: Write the Approval Gate section (contains verbatim sentence)**

`## The Approval Gate` must present a table format `source symbol → test file → CREATE | UPDATE | NO-OP → reason` and contain this exact sentence:

> **Do not write, modify, or run any test until the user has approved this plan.**

- [ ] **Step 7: Write Create-vs-Update Decision + What This Skill Does NOT Do + Reference**

`## Create-vs-Update Decision`:
- **CREATE** — changed symbol has no corresponding test.
- **UPDATE** — a test exists but signature/return shape changed, a new param/branch/error path was added, or an existing assertion now contradicts new behavior.
- **NO-OP** — pure refactor; existing tests remain valid → report "no test change needed" as a valid outcome.

`## What This Skill Does NOT Do`: no frontend/vitest, no E2E/Playwright, no feature-code edits, no broad AC QA (that's `test-ticket`), no product-bug fixes.

`## Reference`: one line pointing to `references/heuristics.md`.

- [ ] **Step 8: Verify the file against the Step-1 acceptance check**

```bash
cd submodules/agentic-sdlc-skills-agents
test -f skills/backend-test-ticket/SKILL.md && echo "exists"
grep -c "Do not write, modify, or run any test until the user has approved this plan." skills/backend-test-ticket/SKILL.md   # expect 1
grep -nE 'app/modules|RolePermission|AuditLog|FSD §' skills/backend-test-ticket/SKILL.md   # expect no non-example hits
head -3 skills/backend-test-ticket/SKILL.md | grep -q 'name: backend-test-ticket' && echo "frontmatter ok"
```
Expected: `exists`, count `1`, no stray project-rule hits, `frontmatter ok`.

- [ ] **Step 9: Commit (in the submodule repo)**

```bash
cd submodules/agentic-sdlc-skills-agents
git add skills/backend-test-ticket/SKILL.md
git commit -m "Add backend-test-ticket SKILL.md"
```

---

## Task 2: Author `references/heuristics.md` in the submodule

**Files:**
- Create: `submodules/agentic-sdlc-skills-agents/skills/backend-test-ticket/references/heuristics.md`

**Interfaces:**
- Consumes: the workflow section names from Task 1 (Steps 2–7) — this file elaborates them.
- Produces: the detection recipes + decision examples referenced by `SKILL.md` `## Reference`.

- [ ] **Step 1: Acceptance check**

The file must contain four sections: `## Detecting the test setup`, `## Locating the code delta`, `## Create vs Update: worked examples`, `## Self-heal policy`. It must include at least two concrete worked examples (one CREATE, one UPDATE) and must label any RIP-specific detail as an example.

- [ ] **Step 2: Write `## Detecting the test setup`**

Recipe list the skill follows to learn a repo:
- Runner/config: read `pyproject.toml` (`[tool.pytest.ini_options]`), else `pytest.ini`/`setup.cfg`/`tox.ini`. Record the invocation (`pytest`, `python -m pytest`, markers, coverage flags).
- Test layout: locate the tests root and naming (`tests/`, `test_*.py`, `*_test.py`, mirror-of-source vs flat).
- Fixtures: read every `conftest.py`; identify the HTTP client fixture, the db/session fixture, and any auth/login helper (e.g. a `login_as` / token fixture). These are the seams new tests must reuse.
- Style: detect async (`pytest.mark.asyncio`, `async def test_`, `httpx.AsyncClient`) vs sync (`TestClient`); detect framework (FastAPI/Flask/Django) and ORM.

- [ ] **Step 3: Write `## Locating the code delta`**

- Find the ticket branch: `git branch -a --list "*PROJ-123*"`; or commits: `git log --all --oneline --grep "PROJ-123"`.
- Diff vs the repo's main branch (detect it: `git symbolic-ref refs/remotes/origin/HEAD` or fall back to `main`/`master`): `git diff <main>...<ticket-ref> --name-only` then per-file `git diff`.
- Fallback with no branch/commits: parse ticket description for module/file/endpoint names; `grep`/`codegraph` to resolve to real files.
- Filter the changed set: keep source under the app package; drop `tests/`, `alembic/`/migrations, `*.md`, config.

- [ ] **Step 4: Write `## Create vs Update: worked examples`**

Include at least these two (label as examples, keep generic):

*CREATE example:* a new endpoint/function appears in the diff with no matching `test_*`. → create a test file mirroring the source path, reuse the detected client + auth fixtures, cover happy path + each new error branch.

*UPDATE example:* an existing function gains environment-dependent behavior — e.g. an auth cookie's `secure` flag becomes `not DEBUG and not TESTING`. An auth test already exists. → **UPDATE** it: add a regression case asserting the new behavior under the new condition, rather than creating a new file.

- [ ] **Step 5: Write `## Self-heal policy`**

- After writing, run only the affected tests first (fast feedback), then the file/module.
- If a test fails because the *test* is wrong (stale expectation, misused fixture), fix the test and re-run.
- If a test fails because the *code* is wrong, STOP editing tests: report the suspected product bug with the failing assertion and reproduction. Never modify feature code to make a test pass.

- [ ] **Step 6: Verify + commit (submodule)**

```bash
cd submodules/agentic-sdlc-skills-agents
grep -c '^## ' skills/backend-test-ticket/references/heuristics.md   # expect >= 4
git add skills/backend-test-ticket/references/heuristics.md
git commit -m "Add backend-test-ticket heuristics reference"
```
Expected: count ≥ 4.

---

## Task 3: Register the skill in the submodule `install.sh`

**Files:**
- Modify: `submodules/agentic-sdlc-skills-agents/install.sh` (the `SKILLS=( ... )` array)

**Interfaces:**
- Consumes: the directory name `backend-test-ticket` from Task 1.
- Produces: installability via the standard installer.

- [ ] **Step 1: Add the entry**

In the `SKILLS=(` array, after `"implement-sprint"`, add a new line:
```bash
  "backend-test-ticket"
```

- [ ] **Step 2: Verify**

```bash
cd submodules/agentic-sdlc-skills-agents
grep -q '"backend-test-ticket"' install.sh && echo "registered"
```
Expected: `registered`.

- [ ] **Step 3: Commit (submodule)**

```bash
cd submodules/agentic-sdlc-skills-agents
git add install.sh
git commit -m "Register backend-test-ticket in installer"
```

---

## Task 4: Install into this project and record the submodule bump

**Files:**
- Create: `.claude/skills/backend-test-ticket/SKILL.md` (copy)
- Create: `.claude/skills/backend-test-ticket/references/heuristics.md` (copy)
- Modify: the superproject's recorded submodule commit (staged as the `submodules/agentic-sdlc-skills-agents` gitlink)

**Interfaces:**
- Consumes: authored files from Tasks 1–2, installer from Task 3.
- Produces: a working, invocable skill in this repo.

- [ ] **Step 1: Copy the skill into the project skills dir**

```bash
cp -r submodules/agentic-sdlc-skills-agents/skills/backend-test-ticket .claude/skills/backend-test-ticket
```

- [ ] **Step 2: Verify the copy**

```bash
test -f .claude/skills/backend-test-ticket/SKILL.md && test -f .claude/skills/backend-test-ticket/references/heuristics.md && echo "installed"
```
Expected: `installed`.

- [ ] **Step 3: Commit to the superproject branch**

```bash
git add .claude/skills/backend-test-ticket submodules/agentic-sdlc-skills-agents
git commit -m "$(cat <<'EOF'
Add backend-test-ticket skill

Jira-ticket-driven backend pytest maintenance skill: locates the code delta,
decides CREATE vs UPDATE vs NO-OP per test file, gates on approval, then
writes and runs tests. Authored in the skills submodule and installed here.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Dry-run validation against a real ticket

**Files:** none (validation only).

**Interfaces:**
- Consumes: the installed skill from Task 4.

- [ ] **Step 1: Pick a known-good target**

Use a recent ticket whose code delta is already understood (e.g. the auth-cookie `secure` fix). Confirm the skill appears in the available-skills list (restart of the session picks up new skills).

- [ ] **Step 2: Invoke and stop at the gate**

Run the skill against the ticket. Verify it:
1. Passes the Jira guard (or prints the setup hint if MCP is off).
2. Produces a code-delta file list from git diff.
3. Detects the pytest setup (names the runner command + the `login_as`/client/db fixtures from `backend/tests/conftest.py`).
4. Emits a CREATE/UPDATE/NO-OP table.
5. **Stops for approval and writes nothing** before you respond.

- [ ] **Step 3: Record the outcome**

If any of the five checks fail, capture which step of `SKILL.md` was ambiguous and fix that section (loop back to Task 1/2). If all pass, the skill is done — do **not** approve the write during this dry run unless you actually want the tests.

---

## Self-Review

**Spec coverage:**
- Boundary / standalone / backend-pytest-only → Task 1 Steps 2–3, 7; `What This Skill Does NOT Do`. ✓
- Trigger + Jira guard → Task 1 Steps 2, 4. ✓
- Workflow steps 0–8 → Task 1 Step 5. ✓
- Locate code (git diff + ticket refs fallback) → Task 1 Step 5 (Step 2), Task 2 Step 3. ✓
- Auto-detection / portability → Task 1 Step 5 (Step 3), Task 2 Step 2. ✓
- Create/Update/No-op heuristics → Task 1 Step 7, Task 2 Step 4. ✓
- Approval gate → Task 1 Step 6. ✓
- Self-heal / report-don't-fix bugs → Task 1 Step 3, Task 2 Step 5. ✓
- Files & location (submodule + install.sh + install) → Tasks 1–4. ✓

**Placeholder scan:** No "TBD/TODO/implement later". Verbatim blocks provided for frontmatter, Jira guard, approval sentence. ✓

**Type/name consistency:** Directory `backend-test-ticket`, section names, and the approval sentence are identical across Tasks 1, 4, and 5. Frontmatter key set (`name`, `description`) matches Global Constraints. ✓
