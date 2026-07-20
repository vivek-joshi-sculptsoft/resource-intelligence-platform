---
name: qa
description: "Multi-agent quality gate on the current branch. Dispatches to code-reviewer, security-reviewer, and qa-engineer subagents in parallel with fresh context, aggregates scores, and blocks /ship unless total >= 85/100. Run after /implement-ticket or /implement-sprint, before /ship. Triggers on: 'qa', 'quality check', 'review this branch', 'run qa', 'quality gate', or any request to review the current implementation before shipping."
---

# QA Gate — Multi-Agent Review

You are a QA orchestrator. You do NOT review code yourself — you delegate to
specialized subagents with fresh context, aggregate their findings, and enforce
a quality gate.

## Core Principle

**Never review your own implementation.** The code-reviewer, security-reviewer,
and qa-engineer agents each get their own context window with only the branch
diff and project docs. They cannot see your implementation conversation.

## Workflow

### Step 1: Verify branch state

1. Confirm you are on a feature/fix branch, NOT main:
   `git branch --show-current` — refuse to proceed if on main.
2. Run the full test suite: `cd backend && python -m pytest tests/ -q`
3. Run frontend lint: `cd frontend && npx tsc -b --noEmit`
4. If either fails, STOP — fix before QA review.

### Step 2: Compute the diff

```bash
git diff main...HEAD --stat
git diff main...HEAD
```

Save the diff context — the agents will need it.

### Step 3: Dispatch reviewers (parallel)

Delegate to all three agents. Each gets the branch diff and instructions to
load CLAUDE.md, FSD, BUSINESS-RULES, and ACCESS-MATRIX as context.

1. **code-reviewer agent** → scores /40 correctness + /10 maintainability
2. **security-reviewer agent** → scores /20 security
3. **qa-engineer agent** → scores /30 coverage + edge cases

### Step 4: Aggregate and gate

| Agent | Max | Blocker threshold |
|---|---|---|
| Code reviewer | 50 | Any "blocker" finding = auto-fail |
| Security reviewer | 20 | Any "critical" finding = auto-fail |
| QA engineer | 30 | Any AC marked UNCOVERED = auto-fail |
| **Total** | **100** | **Must be >= 85 to pass** |

### Step 5: Report and decide

Print the QA report:

```
## QA Report — <branch-name>
### Code Review: XX/50
[findings]
### Security Review: XX/20
[findings]  
### QA Coverage: XX/30
[findings]

### TOTAL: XX/100 — PASS ✅ / FAIL ❌
```

**If FAIL (score < 85 or any blocker/critical/uncovered):**
1. Fix the findings yourself — write a failing test FIRST for each bug found,
   then fix the code, then re-run the test.
2. Re-run Step 3 (fresh agent review on the updated diff). Max 2 retry loops.
3. If still failing after 2 retries, STOP and report — human must intervene.

**If PASS (score >= 85, no blockers):**
Tell the user: "QA passed (XX/100). Run `/ship` to open a PR."

Do NOT open a PR yourself. That is /ship's job.
