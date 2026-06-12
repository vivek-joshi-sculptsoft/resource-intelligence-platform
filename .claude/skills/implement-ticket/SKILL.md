---
name: implement-ticket
description: "Pre-implementation gate that updates JIRA ticket statuses before coding begins. Fetches ticket details and available transitions from Jira, confirms status changes with the user, optionally assigns tickets, then transitions them and hands off to implementation. Triggers on: 'implement PROJ-123', 'start working on PROJ-123', 'pick up ticket', 'work on this ticket', 'implement these tickets', 'start PROJ-123 PROJ-456', 'start sprint N', 'execute sprint N', 'begin sprint N', 'start executing sprint N', 'run sprint N', 'kick off sprint N', or any request to begin implementation of one or more JIRA tickets or an entire sprint. Also auto-detects when a user describes work that maps to a specific ticket. Supports stories, tasks, and sub-tasks — not epics or bugs."
---

# Implement Ticket Skill

You are a pre-implementation gate. Before any code is written for a JIRA ticket, you ensure the ticket's status is correctly transitioned, the user confirms the changes, and then you hand off to the actual implementation work.

You are not a ticket manager or a project planner. You handle the narrow but critical moment between "I want to work on this" and "let me start coding" — making sure the ticket trail reflects reality.

## Core Principles

**No silent status changes.** Always show the user what you intend to change and wait for confirmation. Different Jira projects have different workflows — never assume what the statuses are.

**Discover, don't assume.** Fetch available transitions from Jira at runtime. Never hardcode status names like "In Progress" or "To Do" — workflows vary across projects and issue types.

**Batch-friendly.** When implementing multiple tickets, fetch all statuses, present one consolidated confirmation, and apply the same target status to all tickets.

**Scope: stories, tasks, and sub-tasks only.** Do not transition epics or bugs through this skill. If a user provides an epic key, explain that this skill handles stories/tasks/sub-tasks and suggest they specify the child tickets instead.

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

## Workflow

### Step 0: Identify Tickets

There are two paths into this step: **ticket-level** and **sprint-level**.

#### Path A: Ticket Keys Provided

Extract ticket keys from the user's message. Ticket keys follow the pattern `{PROJECT}-{NUMBER}` (e.g., `PROJ-123`, `ENG-45`).

**If ticket keys found:** proceed with those keys.

**If multiple tickets:** collect all keys and process them as a batch.

#### Path B: Sprint-Level Command

Detect sprint-level commands: `start sprint N`, `execute sprint N`, `begin sprint N`, `start executing sprint N`, `run sprint N`, `kick off sprint N`, or similar phrasing that references a sprint number.

When a sprint-level command is detected:

1. **Locate sprint ticket file.** Read `tickets/phase-1/` (or `tickets/phase-2/`, etc.) to find the sprint file matching the number. Sprint files follow the pattern `sprint-N-*.md` (e.g., `sprint-1-auth.md`, `sprint-2-data-foundation.md`).

2. **Extract ticket keys from the sprint file.** Sprint files contain story headers like `### S1-01: Title` with JIRA ticket keys in the content. Look for JIRA project keys (e.g., `VRIP-19`). If ticket keys aren't directly in the sprint file, use the story identifiers (e.g., `S1-01`) and cross-reference with `shared/TRACEABILITY.yaml` or search JIRA via JQL: `project = {PROJECT} AND sprint = {sprint_name}`.

3. **If no JIRA keys found in files:** query JIRA directly using `searchJiraIssuesUsingJql` with JQL like `project = VRIP AND sprint in openSprints()` or `project = VRIP AND sprint = "Sprint 1"` to find all tickets in that sprint.

4. **Present the full ticket list** to the user for confirmation before proceeding:
   ```
   Found {N} tickets in Sprint {X}:

   | # | Ticket | Title | Type | Status |
   |---|--------|-------|------|--------|
   | 1 | PROJ-19 | Login/logout API | Story | To Do |
   | 2 | PROJ-20 | Token refresh | Story | To Do |
   ...

   Implement all {N} tickets in order? Or specify which ones to start with.
   ```

5. **User can narrow scope:** If the user says "just the first 3" or "only backend tickets", filter accordingly.

6. Proceed to Step 1 with the confirmed ticket list.

#### Path C: No Tickets or Sprint Identified

**If no ticket keys found and no sprint reference, but user describes work:** ask the user for the specific ticket key(s):
```
Which ticket(s) should I update before starting? Provide the JIRA key(s) — e.g., PROJ-123 or PROJ-123, PROJ-124, PROJ-125.
Or specify a sprint: "start sprint 1"
```

### Step 1: Fetch Ticket Details

For each ticket key, fetch the issue from Jira using `getJiraIssue`. Collect:
- Issue key
- Summary (title)
- Issue type (story, task, sub-task, epic, bug, etc.)
- Current status
- Current assignee (if any)

**Filter by type:** Only proceed with stories, tasks, and sub-tasks. If any ticket is an epic or bug, flag it:
```
{KEY} is a {type} — this skill handles stories, tasks, and sub-tasks only.
Skipping {KEY}. Want me to list its child stories/tasks instead?
```

If ALL tickets are filtered out, stop.

### Step 2: Fetch Available Transitions

For each valid ticket, call `getTransitionsForJiraIssue` to get the list of available transitions from the current status.

**If transitions are returned:** identify the most likely "in progress" transition. Look for transition names containing (case-insensitive): `in progress`, `in development`, `start`, `begin`, `active`, `working`. If multiple candidates exist, present all options.

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

1. Call `transitionJiraIssue` with the confirmed transition ID.
2. If assignment was requested, call `editJiraIssue` to set the `assignee` field.
3. Report success or failure per ticket:

```
## Status Updates Applied

✓ PROJ-123 → In Progress (assigned to you)
✓ PROJ-124 → In Progress (assigned to you)
✗ PROJ-125 → Failed: {error message}
```

If any transition fails, report the error and ask if the user wants to retry or skip that ticket.

### Step 5: Hand Off to Implementation

After all transitions are applied, read each ticket's full description and acceptance criteria from Jira (already fetched in Step 1). Present the implementation brief:

```
## Ready to Implement

### PROJ-123: {Title}
**Description:** {description summary}
**Acceptance Criteria:**
- {criterion 1}
- {criterion 2}

### PROJ-124: {Title}
**Description:** {description summary}
**Acceptance Criteria:**
- {criterion 1}

Starting implementation...
```

Then begin the actual implementation work:

1. Read CLAUDE.md or project instructions for coding conventions.
2. Read any spec files referenced in the ticket description (REQUIREMENTS.md, SCHEMA.md, API.md, SCREENS.md, etc.).
3. Implement the ticket following project conventions.
4. Run tests if test infrastructure exists.
5. Run linter if configured.

After implementation is complete for each ticket, ask:
```
Implementation complete for {KEY}. Should I transition it to done/review?
  a) Yes — move to {discovered "done" or "in review" status}
  b) No — leave as In Progress
```

---

## Multi-Ticket Implementation Order

When implementing multiple tickets:

1. Check for dependencies between the tickets (look at ticket links, `blocked by` relationships).
2. Implement in dependency order — prerequisites first.
3. If no dependencies, implement in the order the user provided them.
4. Complete each ticket fully before starting the next.
5. Transition each ticket's status after its implementation is done (with user confirmation per step 5).

---

## Edge Cases

### Ticket already in target status
If a ticket is already "In Progress" (or equivalent), note it and skip:
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
The Jira MCP tools require a `cloudId`. On first use:
1. Call `getAccessibleAtlassianResources` to list available Jira sites.
2. If exactly one site: use it automatically.
3. If multiple sites: ask the user which site to use.
4. Cache the cloudId for the rest of the session.

---

## Reference Files

| File | When to Read | Purpose |
|------|-------------|---------|
| `references/workflow-checklist.md` | At the start of every invocation | Runtime checklist to ensure no step is skipped |
