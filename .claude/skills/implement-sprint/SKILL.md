---
name: implement-sprint
description: "Sprint-level orchestrator that fetches all tickets from a Jira sprint and implements them sequentially using the /implement-ticket skill. Triggers on: 'implement sprint N', 'execute sprint N', 'start sprint N', 'run sprint N', 'kick off sprint N', 'begin sprint N', 'implement the current sprint', 'implement active sprint', 'implement sprint Sprint-Name', or any request to implement all tickets in a sprint. Handles sprint discovery, ticket ordering by dependency, progress tracking, and sequential delegation to /implement-ticket."
---

# Implement Sprint Skill

You are a sprint-level orchestrator. Given a sprint identifier (number, name, or "current/active"), you fetch all tickets in that sprint from Jira, present them for confirmation, then implement each one sequentially by invoking the `/implement-ticket` skill.

You are not a ticket implementer yourself. You discover what needs to be done, establish the order, and delegate each ticket to `/implement-ticket` which handles status transitions, confirmation, and actual implementation.

## Core Principles

**Sprint as the unit of work.** The user thinks in sprints — you translate that into an ordered list of tickets and drive them through one at a time.

**Workflow-first.** Before touching any ticket, discover its Jira workflow — available transitions and reachable statuses. Never assume status names like "In Progress" or "Done" exist. Different projects and issue types have different workflows. Surface workflow blockers (no valid transition, permissions) in the sprint plan so the user can resolve them before implementation begins.

**Dependency-aware ordering.** Fetch ticket links and blocked-by relationships from Jira. Implement prerequisites before dependents. If no explicit dependencies, fall back to ticket type ordering: infrastructure/config → data/schema → backend/API → frontend/UI → integration/glue.

**Progress visibility.** After each ticket completes, show a sprint progress summary so the user always knows where they stand.

**Delegate, don't duplicate.** Each ticket's status transitions, confirmation, and implementation are handled by `/implement-ticket`. This skill handles sprint-level concerns only: discovery, ordering, workflow pre-check, progress, and completion.

---

## Jira MCP Requirement

This skill requires Jira MCP tools. At startup, check for tools containing `atlassian` or `jira` in the name.

**If Jira MCP is available:** proceed with the workflow below.

**If Jira MCP is not available:** tell the user:
```
This skill requires a Jira connection to fetch sprint tickets.
Set up the Atlassian MCP:
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
Then try again.
```

---

## Superpowers Interaction

This skill orchestrates a full sprint by delegating each ticket to
`/implement-ticket`. **Skip the Superpowers brainstorming and planning skills**
at the sprint orchestration level — this skill's Steps 1–5 (sprint discovery,
ticket ordering, workflow pre-check, plan presentation, confirmation) replace
Superpowers' planning phase entirely with Jira-driven context.

When `/implement-ticket` is invoked for each ticket (Step 6), the same rule
applies: Superpowers planning is skipped, but TDD enforcement and code review
remain active during the coding steps.

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

## Workflow

### Step 0: Discover Cloud ID

On first use in a session:
1. Call `getAccessibleAtlassianResources` to list available Jira sites.
2. If exactly one site: use it automatically.
3. If multiple sites: ask the user which site to use.
4. Cache the cloudId for the rest of the session.

### Step 1: Identify the Sprint

Parse the user's message to determine which sprint to implement. Three paths:

#### Path A: Sprint Number or Name Given

User says "implement sprint 3" or "implement sprint Auth-Foundation".

1. Search for the sprint using JQL via `searchJiraIssuesUsingJql`:
   - By number: `sprint = "Sprint 3"` or `sprint = 3`
   - By name: `sprint = "Auth-Foundation"`
2. If no results, try broader search: `sprint in openSprints()` and match by name/number from the results.
3. If still no results, ask the user for clarification.

#### Path B: Current/Active Sprint

User says "implement the current sprint" or "implement active sprint".

1. Query: `sprint in openSprints() AND project = {PROJECT}`
2. If the project key is unknown, ask the user: "Which Jira project? (e.g., PROJ, ENG)"
3. If multiple active sprints found, present them and ask which one.

#### Path C: No Sprint Identified

Ask the user:
```
Which sprint should I implement? Provide either:
- A sprint number: "sprint 3"
- A sprint name: "Auth-Foundation"
- Or say "current sprint" for the active sprint
```

### Step 2: Fetch All Sprint Tickets

Once the sprint is identified:

1. Query all tickets in the sprint using `searchJiraIssuesUsingJql`:
   - JQL: `sprint = "{sprint_name}" ORDER BY rank ASC`
   - Or: `sprint = {sprint_id} ORDER BY rank ASC`
2. For each ticket, collect: key, summary, issue type, status, assignee, priority.
3. Filter to supported types: stories, tasks, sub-tasks only. Flag and exclude epics and bugs:
   ```
   Skipping {KEY} ({type}) — /implement-ticket handles stories, tasks, and sub-tasks only.
   ```
4. If ALL tickets are filtered out, stop.

### Step 3: Discover Ticket Workflows

For each ticket, call `getTransitionsForJiraIssue` to discover the available transitions from its current status. This is the **workflow-first gate** — no status change will be attempted without first knowing what the Jira workflow allows.

For each ticket, record:
- **Current status** (from Step 2)
- **Available transitions** — the list of transitions the ticket can take from its current status
- **Start-work transition** — the most likely "begin implementation" transition. Look for names containing (case-insensitive): `in progress`, `in development`, `start`, `begin`, `active`, `working`
- **Done/review transition** — the most likely "completed" transition. Look for names containing: `done`, `review`, `resolved`, `closed`, `complete`

**Classify each ticket's workflow readiness:**

| Classification | Condition | Action |
|---------------|-----------|--------|
| Ready | Has a valid start-work transition | Proceed normally |
| Already started | Current status already matches an in-progress state | Skip start transition, implement directly |
| Already done | Current status is done/closed/resolved | Skip entirely |
| Workflow blocked | No valid start-work transition available | Flag for user — may need manual Jira action |
| Multiple candidates | More than one plausible start-work transition | Present options in sprint plan, let user choose |

**If transitions can't be fetched** for a ticket (API error, permissions), flag it:
```
⚠ Could not fetch workflow for {KEY}. Transitions will be discovered per-ticket by /implement-ticket.
```

This workflow data is used in Step 5 (sprint plan) to show transition paths and in Step 6 to inform `/implement-ticket` what transitions to use.

### Step 4: Determine Implementation Order

1. For each ticket, call `getJiraIssue` to fetch issue links (blocked-by, depends-on relationships).
2. Build a dependency graph from the ticket links.
3. Topologically sort tickets by dependencies — prerequisites first.
4. If no explicit dependencies, order by type heuristic:
   - Infrastructure / config tickets first
   - Data model / schema tickets second
   - Backend / API tickets third
   - Frontend / UI tickets fourth
   - Integration / glue tickets last
   - Within the same category, preserve Jira rank order.
5. If circular dependencies are detected, flag them and fall back to Jira rank order.

### Step 5: Present Sprint Plan

Present the full sprint plan to the user, including the discovered workflow transitions:

```
## Sprint {N}: {Sprint Name}

Found {total} tickets ({filtered} skipped — epics/bugs).

### Workflow Summary

Jira workflow for this sprint's tickets:
- Start transition: "{discovered start-work transition name}" (e.g., "In Progress", "Start Development")
- Done transition: "{discovered done transition name}" (e.g., "Done", "In Review")

{If different tickets have different workflows}:
Note: Tickets in this sprint use {N} different workflows. Transitions shown per ticket below.

### Implementation Order

| # | Ticket | Title | Type | Current Status | → Start Transition | Depends On |
|---|--------|-------|------|---------------|-------------------|------------|
| 1 | PROJ-101 | DB schema setup | Task | To Do | → In Progress | — |
| 2 | PROJ-102 | User auth API | Story | To Do | → In Progress | PROJ-101 |
| 3 | PROJ-103 | Login screen | Story | To Do | → Start Development | PROJ-102 |
| 4 | PROJ-104 | Dashboard layout | Story | In Progress | (already started) | — |
| 5 | PROJ-105 | Final integration | Story | To Do | ⚠ No valid transition | PROJ-103 |
...

{If any tickets are already done or in review}:
Note: {N} ticket(s) already completed — will be skipped.

{If any tickets are workflow-blocked}:
⚠ {N} ticket(s) have no valid start-work transition. These need manual Jira action or will be skipped.

{If any tickets have multiple candidate transitions}:
{KEY} has multiple start transitions available: "In Progress", "Start Development". Which one?

Implement all {N} tickets in this order?
  a) Yes — start from ticket #1
  b) Start from ticket #N (skip already-done tickets)
  c) Let me pick specific tickets
  d) Change the order
```

**If the user chooses c):** Let them specify which tickets to include. Re-present the filtered list.

**If the user chooses d):** Let them reorder. Re-present for confirmation.

**Workflow-blocked tickets:** If the user confirms the plan with workflow-blocked tickets included, those tickets will still be passed to `/implement-ticket` which will attempt to discover transitions at execution time (workflow state may have changed by then). If the user wants to skip them, they can use option c).

### Step 6: Sequential Implementation

For each ticket in the confirmed order:

1. **Show progress header with workflow context:**
   ```
   ─────────────────────────────────────
   Sprint Progress: {completed}/{total} tickets done
   Now starting: #{position} — {KEY}: {Title}
   Workflow: {current_status} → {start_transition} → ... → {done_transition}
   ─────────────────────────────────────
   ```

2. **Invoke `/implement-ticket` for the current ticket.** Pass the workflow context discovered in Step 3 so `/implement-ticket` can use the pre-discovered transitions rather than re-fetching blindly. `/implement-ticket` handles:
   - Fetching ticket details (may use cached data from Step 2)
   - Confirming status change with user using the discovered workflow transitions
   - Transitioning to the discovered start-work status
   - Reading ticket description and acceptance criteria
   - Implementing the ticket
   - Offering to transition to the discovered done/review status

3. **After `/implement-ticket` completes**, re-fetch the ticket's current status from Jira to confirm the transition succeeded, then show sprint progress:
   ```
   ## Sprint Progress

   | # | Ticket | Title | Status |
   |---|--------|-------|--------|
   | 1 | PROJ-101 | DB schema setup | ✓ Done |
   | 2 | PROJ-102 | User auth API | ✓ In Review |
   | 3 | PROJ-103 | Login screen | ← Up Next |
   | 4 | PROJ-104 | Dashboard layout | Pending |

   Continue with #{next} — {KEY}: {Title}? (y/n/skip)
   ```

4. **User can control flow:**
   - **y** or Enter: proceed to next ticket
   - **n**: pause the sprint — offer to resume later
   - **skip**: skip this ticket, move to the next one

5. **Commit strategy:** After each ticket's implementation, ensure changes are committed before moving to the next ticket. This keeps the git history clean with one logical commit per ticket.

### Step 7: Sprint Completion

After all tickets are processed:

```
## Sprint {N} Complete

| # | Ticket | Title | Start Status | Final Status | Result |
|---|--------|-------|-------------|-------------|--------|
| 1 | PROJ-101 | DB schema setup | To Do | Done | ✓ Implemented |
| 2 | PROJ-102 | User auth API | To Do | In Review | ✓ Implemented |
| 3 | PROJ-103 | Login screen | To Do | In Progress | ✗ Failed |
| 4 | PROJ-104 | Dashboard layout | To Do | To Do | ⊘ Skipped |

{completed}/{total} tickets implemented. {skipped} skipped. {failed} failed.
```

---

## Edge Cases

### Workflow-related

#### No valid start-work transition
If `getTransitionsForJiraIssue` returns transitions but none match start-work patterns, present the full list of available transitions to the user and ask which one to use:
```
{KEY} (currently "{status}") has these transitions available:
  1) "Backlog"
  2) "Selected for Development"
  3) "Blocked"
Which transition represents starting work on this ticket?
```

#### Different workflows across tickets
If tickets in the sprint belong to different Jira projects or issue types with different workflows, group them by workflow in the sprint plan and show the transition path per group.

#### Transition fails at execution time
If a transition that was available during Step 3 (workflow discovery) fails when `/implement-ticket` attempts it (workflow may have changed, permissions, conditions), the failure is handled by `/implement-ticket`'s error handling. After failure, re-fetch the ticket's transitions to check if the workflow state changed.

#### Workflow permissions
If `getTransitionsForJiraIssue` returns an empty list, this usually means the user lacks permission to transition the ticket. Flag it:
```
{KEY}: No transitions available — you may not have permission to change this ticket's status.
Proceed with implementation anyway (leave status unchanged)? Or skip this ticket?
```

### General

### Ticket already implemented
If a ticket's status indicates it's already done (Done, Closed, Resolved, etc.), skip it automatically and note it in the progress table.

### Ticket in progress by someone else
If a ticket is assigned to someone else and is already In Progress, flag it:
```
{KEY} is assigned to {person} and already In Progress.
  a) Implement anyway (will be handled by /implement-ticket confirmation)
  b) Skip this ticket
```

### Sprint has no tickets
```
Sprint {N} has no tickets (or all tickets are epics/bugs which are not supported).
Check your sprint in Jira or provide a different sprint.
```

### Mid-sprint resume
If the user says "continue sprint" or "resume sprint", detect which tickets are already done (by status) and start from the first non-done ticket.

### Implementation failure
If `/implement-ticket` fails or the user aborts a ticket mid-implementation:
```
{KEY} was not completed.
  a) Retry this ticket
  b) Skip and continue to next
  c) Pause the sprint
```

### Large sprints
If a sprint has more than 15 tickets, warn the user:
```
Sprint {N} has {count} tickets. This will be a long session.
Want to implement all {count}, or pick a subset to start with?
```

---

## Reference Files

| File | When to Read | Purpose |
|------|-------------|---------|
| `references/workflow-checklist.md` | At the start of every invocation | Runtime checklist to ensure no step is skipped |
