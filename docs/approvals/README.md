# Spec Approval Gate (Gate 1)

This directory holds approval markers that unlock implementation work.
Without a marker, /implement-ticket, /implement-sprint, and /ship refuse to run.

## How to approve

After you have personally reviewed:
- `fsd/FSD.md` (functional spec)
- `techstack/` and `techstack/decisions/` (ADRs)
- The relevant `modules/{module}/` specs (REQUIREMENTS, SCHEMA, API, SCREENS)

Create the marker:

```bash
echo "approved-by: <your-name> $(date -u +%F)" > docs/approvals/SPEC-APPROVED
git add docs/approvals/SPEC-APPROVED
git commit -m "chore: approve spec for implementation"
```

## Rules

1. Only a human creates this file. The PreToolUse hook in settings.json blocks
   Claude from creating it (any bash command containing "SPEC-APPROVED" + a
   write operation is blocked with exit code 2).

2. Any run of /repo-architect or /fsd-generator that produces significant design
   changes SHOULD delete this marker (the skill instructions tell Claude to do so).
   This re-closes the gate until a human re-approves.

3. The marker is checked at the start of /implement-ticket, /implement-sprint,
   and /ship. If missing, they stop and tell you to review the spec.

## Why this exists

Without this gate, Claude can go from "here's a rough idea" to "I've built 12
endpoints" without a human ever reading the design. The 5 minutes you spend
reading the spec saves days of rework.
