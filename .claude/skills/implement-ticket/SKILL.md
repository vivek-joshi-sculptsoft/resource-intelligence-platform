---
name: implement-ticket
description: "Pre-implementation gate that updates JIRA ticket statuses before coding begins. Fetches ticket details and available transitions from Jira, confirms status changes with the user, optionally assigns tickets, then transitions them and hands off to implementation. Triggers on: 'implement PROJ-123', 'start working on PROJ-123', 'pick up ticket', 'work on this ticket', 'implement these tickets', 'start PROJ-123 PROJ-456', or any request to begin implementation of one or more JIRA tickets. Also auto-detects when a user describes work that maps to a specific ticket. Supports stories, tasks, and sub-tasks — not epics or bugs. For sprint-level implementation, use /implement-sprint instead."
---

# Implement Ticket Skill

You are a pre-implementation gate. Before any code is written for a JIRA ticket, you ensure the ticket's status is correctly transitioned, the user confirms the changes, and then you hand off to the actual implementation work.

You are not a ticket manager or a project planner. You handle the narrow but critical moment between "I want to work on this" and "let me start coding" — making sure the ticket trail reflects reality.

## Core Principles

**No silent status changes.** Always show the user what you intend to change and wait for confirmation — unless called from `/implement-sprint` which already confirmed the plan.

**Discover, don't assume.** Fetch available transitions from Jira at runtime. Never hardcode status names like "In Progress" or "To Do" — workflows vary across projects and issue types.

**Batch-friendly.** When implementing multiple tickets, fetch all statuses, present one consolidated confirmation, and apply the same target status to all tickets.

**Scope: stories, tasks, and sub-tasks only.** Do not transition epics or bugs through this skill. If a user provides an epic key, explain that this skill handles stories/tasks/sub-tasks and suggest they specify the child tickets instead.

**Sprint-aware.** When called from `/implement-sprint`, workflow context (transition IDs, assignment, cloudId) is already known. Skip redundant discovery and confirmation steps — go straight to execution and implementation.

---

## Jira MCP Requirement

This skill requires Jira MCP tools. At startup, check for tools containing `atlassian` or `jira` in the name.

**If Jira MCP is available:** proceed with the workflow below.

**If Jira MCP is not available:** tell the user:
```
This skill requires a Jira connection to fetch ticket statuses and transitions.
Set up the Atlassian MCP:
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
Then try again.
```

---

## Superpowers Interaction

This skill has its own Jira-driven planning workflow (fetch ticket → read module
specs → plan → implement). **Skip the Superpowers brainstorming and planning
skills** when this skill is active — they would produce a redundant planning
pass before Step 5 runs, wasting tokens without adding context this skill
doesn't already gather from Jira and the module files.

Superpowers skills that **remain active and welcome** during implementation:
- **TDD enforcement** — red/green/refactor during Step 2 (backend) and Step 3
  (frontend) is exactly what CLAUDE.md Step 2.5 requires
- **Code review** — Superpowers' self-review during implementation complements
  (but does not replace) the post-implementation `/qa` gate

In short: Superpowers owns *how* you write code. This skill owns *what* you
write and *in what order*.

---

## Gate 1 Check (Spec Approval)

Before any implementation work, verify the spec has been approved:

```bash
bash scripts/check-gate1.sh
```

If the script exits non-zero (Gate 1 not approved), STOP immediately.
Tell the user:

> Implementation is blocked — the spec has not been approved yet.
> Please review `fsd/FSD.md` and the relevant `modules/` specs, then run:
> ```
> echo "approved-by: <your-name> $(date -u +%F)" > docs/approvals/SPEC-APPROVED
> ```
> See `docs/approvals/README.md` for details.

Do NOT proceed with implementation. Do NOT offer to create the marker yourself.

---

## Two Modes of Operation

### Mode 1: Standalone (user invokes directly)

The user says "implement VRIP-43" or similar. Full workflow: discover → confirm → transition → implement.

### Mode 2: Called from /implement-sprint

The sprint orchestrator has already:
- Discovered the cloudId
- Fetched all ticket details (key, summary, type, status, assignee)
- Discovered available transitions for all tickets
- Confirmed the sprint plan with the user (including implementation order)
- Assigned all tickets to the user
- Transitioned the current ticket to "In Progress"

**When in sprint mode:** skip Steps 0–4 entirely. Jump straight to Step 5 (implementation). The sprint orchestrator passes the ticket key as an argument — use it directly.

**How to detect sprint mode:** If the conversation context shows that `/implement-sprint` is orchestrating (sprint progress headers, sprint plan already confirmed, ticket already transitioned to In Progress), you are in sprint mode. Do not re-ask for confirmation or re-fetch transitions.

---

## Workflow (Standalone Mode)

### Step 0: Identify Tickets

Extract ticket keys from the user's message. Ticket keys follow the pattern `{PROJECT}-{NUMBER}` (e.g., `PROJ-123`, `ENG-45`).

**If ticket keys found:** proceed with those keys.

**If multiple tickets:** collect all keys and process them as a batch.

**If sprint-level command detected** (e.g., "start sprint N", "implement sprint N"): redirect the user to `/implement-sprint` which handles sprint-level orchestration:
```
For sprint-level implementation, use /implement-sprint instead.
It handles ticket discovery, ordering, workflow transitions, and progress tracking across the full sprint.
```

**If no ticket keys found:** ask the user for the specific ticket key(s):
```
Which ticket(s) should I implement? Provide the JIRA key(s) — e.g., PROJ-123 or PROJ-123, PROJ-124, PROJ-125.
For a full sprint, use /implement-sprint.
```

### Step 1: Fetch Ticket Details

For each ticket key, fetch the issue from Jira using `getJiraIssue`. Collect:
- Issue key
- Summary (title)
- Issue type (story, task, sub-task, epic, bug, etc.)
- Current status
- Current assignee (if any)
- Full description and acceptance criteria

**Filter by type:** Only proceed with stories, tasks, and sub-tasks. If any ticket is an epic or bug, flag it:
```
{KEY} is a {type} — this skill handles stories, tasks, and sub-tasks only.
Skipping {KEY}. Want me to list its child stories/tasks instead?
```

If ALL tickets are filtered out, stop.

### Step 2: Fetch Available Transitions

For each valid ticket, call `getTransitionsForJiraIssue` to get the list of available transitions from the current status.

**Identify two transitions:**

1. **Start-work transition** — names containing (case-insensitive): `in progress`, `in development`, `start`, `begin`, `active`, `working`
2. **Done/review transition** — names containing: `done`, `review`, `resolved`, `closed`, `complete`, `code complete`

Record both transition IDs for later use (start-work in Step 4, done/review in Step 5).

**If multiple candidates exist for either:** present all options to the user.

**If no transitions are returned or the call fails:** ask the user what status to move the ticket to:
```
I couldn't fetch available transitions for {KEY} (currently: {status}).
What status should I move it to? Type the exact status name as it appears in your Jira workflow.
```

### Step 3: Present Confirmation

Present a single consolidated table showing all proposed changes:

```
## Pre-Implementation Status Update

| Ticket | Title | Type | Current Status | → New Status |
|--------|-------|------|---------------|-------------|
| PROJ-123 | Build user auth | Story | To Do | In Progress |
| PROJ-124 | Add login API | Sub-task | Open | In Progress |

{If any tickets have an assignee that is not the current user, or are unassigned}:
These tickets are currently {unassigned / assigned to someone else}. Should I assign them to you?
  a) Yes — assign all to me
  b) No — leave assignment as-is
  c) Let me specify per ticket

Proceed with these status changes? (y/n)
```

**If the user says no or wants changes:** let them specify different target statuses per ticket, or remove tickets from the batch. Re-present the updated table for confirmation.

**Assignment flow (if user chose a):** Use `lookupJiraAccountId` with the user's email to find their Jira account ID, then include assignment in the transition step.

**Assignment flow (if user chose c):** Ask per ticket who to assign (me / leave as-is / specific person).

### Step 4: Execute Transitions

For each confirmed ticket:

1. Call `transitionJiraIssue` with the confirmed start-work transition ID.
2. If assignment was requested, call `editJiraIssue` to set the `assignee` field.
3. Report success or failure per ticket:

```
## Status Updates Applied

✓ PROJ-123 → In Progress (assigned to you)
✓ PROJ-124 → In Progress (assigned to you)
✗ PROJ-125 → Failed: {error message}
```

If any transition fails, report the error and ask if the user wants to retry or skip that ticket.

### Step 5: Implement

**This is the entry point when called from /implement-sprint.** In sprint mode, Steps 0–4 are already done — the ticket is In Progress, assigned, and the user confirmed the plan.

Read each ticket's full description and acceptance criteria from Jira (already fetched in Step 1, or available from sprint context). Present the implementation brief:

```
## Ready to Implement

### PROJ-123: {Title}
**Acceptance Criteria:**
- {criterion 1}
- {criterion 2}

Starting implementation...
```

Then begin the actual implementation work:

1. Read CLAUDE.md or project instructions for coding conventions.
2. Read any spec files referenced in the ticket description (REQUIREMENTS.md, SCHEMA.md, API.md, SCREENS.md, etc.).
3. Implement the ticket following project conventions.
4. Run tests if test infrastructure exists.
5. Run linter if configured.

After implementation is complete for each ticket, offer to transition to done/review using the done transition discovered in Step 2 (or re-fetch transitions if in sprint mode):

```
Implementation complete for {KEY}. Transition to done/review?
  a) Yes — move to {done/review status name}
  b) No — leave as In Progress
```

---

## Multi-Ticket Implementation Order

When implementing multiple tickets in standalone mode:

1. Check for dependencies between the tickets (look at ticket links, `blocked by` relationships).
2. Implement in dependency order — prerequisites first.
3. If no dependencies, implement in the order the user provided them.
4. Complete each ticket fully before starting the next.
5. Transition each ticket's status after its implementation is done (with user confirmation per Step 5).

When called from `/implement-sprint`, the sprint orchestrator controls the order and progress tracking.

---

## Edge Cases

### Ticket already in target status
If a ticket is already "In Progress" (or equivalent), note it and skip the transition:
```
PROJ-123 is already "In Progress" — no transition needed.
```

### Ticket in a later status
If a ticket is in "In Review", "Done", "Closed", or similar post-implementation status, flag it:
```
PROJ-123 is currently "{status}" — this is past the implementation stage.
Should I still proceed? Moving backwards in the workflow may require specific permissions.
```

### Permissions error
If the transition fails due to permissions:
```
Cannot transition {KEY}: {error}. You may not have permission for this transition.
Check with your Jira admin or transition the ticket manually, then tell me to proceed with implementation.
```

### Cloud ID discovery
The Jira MCP tools require a `cloudId`. On first use in standalone mode:
1. Call `getAccessibleAtlassianResources` to list available Jira sites.
2. If exactly one site: use it automatically.
3. If multiple sites: ask the user which site to use.
4. Cache the cloudId for the rest of the session.

In sprint mode, the cloudId is already known from the sprint orchestrator's context.

### Sprint-level commands
If the user says "start sprint N", "implement sprint 3", "execute sprint N", or similar:
```
For sprint-level implementation, use /implement-sprint.
It handles ticket discovery, dependency ordering, workflow transitions, and progress tracking.
```

---

## Reference Files

| File | When to Read | Purpose |
|------|-------------|---------|
| `references/workflow-checklist.md` | At the start of every invocation | Runtime checklist to ensure no step is skipped |
