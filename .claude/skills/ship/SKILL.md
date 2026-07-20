---
name: ship
description: "Open a PR for the current feature/fix branch after QA passes. Enforces Gate 2 — never merges, never pushes to main. Triggers on: 'ship', 'open PR', 'create PR', 'ship it', 'ready to merge', or any request to finalize a branch into a pull request."
allowed-tools: Read, Bash, Grep, Glob
---

# Ship — Open PR (Gate 2: human merge only)

You prepare and open a pull request. You NEVER merge it.

## Pre-flight checks (all must pass)

1. **Not on main:** `git branch --show-current` must NOT be main/master
2. **Tests green:** `cd backend && python -m pytest tests/ -q` — all pass
3. **Lint green:** `cd frontend && npx tsc -b --noEmit` — no errors  
4. **QA report exists:** check the conversation history for a QA report with
   score >= 85. If no QA was run, STOP: "Run `/qa` first."

If any check fails, STOP and report what's missing.

## Build the PR

### Detect the ticket

- Parse the branch name for a ticket ID (e.g. `feat/VRIP-43-something` → VRIP-43)
- If Atlassian MCP is available, fetch the ticket for title and AC summary
- If not, derive from the commit messages

### Push and create PR

```bash
git push -u origin $(git branch --show-current)
```

Then create the PR via `gh`:

```bash
gh pr create \
  --title "<type>(<module>): <summary> [<ticket-id>]" \
  --base main \
  --body-file pr-body.md
```

Generate `pr-body.md` with this structure:

```markdown
## Jira ticket
<ticket URL or ID>

## What changed
<2-3 sentence summary of the implementation>

## Test evidence
- Backend: X tests passed, Y new tests added
- E2E: <tier and count if applicable>
- Coverage delta: <if available>

## QA score
<score>/100 — code review XX/50, security XX/20, QA coverage XX/30

## Checklist
- [ ] FSD section references in business logic comments
- [ ] Access control tested for all 7 roles
- [ ] Audit logging on all write operations
- [ ] No hardcoded magic numbers
- [ ] Relationship serialization tests (FK set/null/invalid)

## Rollback plan
<how to revert if this breaks something>
```

### After PR is created

1. If Jira MCP is available: transition the ticket to "In Review"
2. Clean up `pr-body.md`: `rm pr-body.md`
3. Print: "PR opened. Claude CI will post an automated review. A human must
   approve and merge (Gate 2)."

## Hard rules

- NEVER run `gh pr merge` — the PreToolUse hook blocks it, and it's forbidden
- NEVER push to main — always push the feature/fix branch only
- NEVER approve your own PR
- The CI `claude-pr-review.yml` workflow handles the first-pass AI review
  automatically — you don't need to trigger it
