# Implement Ticket — Runtime Workflow Checklist

Read this at the start of every invocation. Use it as a live checklist to ensure no step is skipped.

---

## Mode Detection (Do This First)

- [ ] Check if `/implement-sprint` is orchestrating this invocation
  - Sprint progress headers visible in conversation context?
  - Sprint plan already confirmed by user?
  - Ticket already transitioned to In Progress and assigned?
  - **If YES to all → Sprint Mode.** Skip to Step 5 (Implement). Do not re-confirm, re-fetch, or re-transition.
  - **If NO → Standalone Mode.** Follow full workflow below.

---

## Pre-Flight (Standalone Mode Only)

- [ ] Check for Jira MCP tools (tool names containing `atlassian` or `jira`)
  - If not available → tell user to set up Atlassian MCP, STOP
- [ ] Discover cloudId — call `getAccessibleAtlassianResources`
  - One site → use it
  - Multiple sites → ask user
  - Cache for session

---

## Step 0: Identify Tickets (Standalone Mode Only)

- [ ] Extract ticket keys from user message (pattern: `{PROJECT}-{NUMBER}`)
- [ ] If sprint-level command detected → redirect to `/implement-sprint`, STOP
- [ ] If no keys found → ask user for specific ticket key(s)
- [ ] If multiple keys → collect all, process as batch

---

## Step 1: Fetch Ticket Details (Standalone Mode Only)

For each ticket key:
- [ ] Call `getJiraIssue` — collect: key, summary, type, status, assignee, description, AC
- [ ] Filter by type — only stories, tasks, sub-tasks
  - Epic or bug → flag it, skip it, offer to list child tickets
- [ ] If ALL tickets filtered out → STOP

---

## Step 2: Fetch Available Transitions (Standalone Mode Only)

For each valid ticket:
- [ ] Call `getTransitionsForJiraIssue`
- [ ] Identify **start-work** transition (names containing: in progress, in development, start, begin, active, working)
- [ ] Identify **done/review** transition (names containing: done, review, resolved, closed, complete, code complete)
- [ ] Record both transition IDs for later use
- [ ] If multiple candidates for either → present all options to user
- [ ] If no transitions returned or call fails → ask user for target status name

---

## Step 3: Present Confirmation (Standalone Mode Only)

- [ ] Build consolidated table: Ticket | Title | Type | Current Status | → New Status
- [ ] Check assignee status for all tickets
  - Unassigned or assigned to someone else → ask user:
    - a) Assign all to me
    - b) Leave as-is
    - c) Specify per ticket
- [ ] Present full table and ask for confirmation
- [ ] **WAIT FOR USER CONFIRMATION**
- [ ] If user wants changes → let them modify, re-present table
- [ ] If assignment requested → look up user's Jira account ID via `lookupJiraAccountId`

---

## Step 4: Execute Transitions (Standalone Mode Only)

For each confirmed ticket:
- [ ] Call `transitionJiraIssue` with confirmed start-work transition ID
- [ ] If assignment requested → call `editJiraIssue` to set assignee field
- [ ] Report success/failure per ticket
- [ ] If any fail → report error, ask retry or skip

---

## Step 5: Implement (Both Modes)

**This is the entry point in Sprint Mode.** In standalone mode, you reach here after Steps 0–4.

- [ ] Read each ticket's full description and acceptance criteria
  - Standalone: from Step 1 data
  - Sprint mode: from conversation context or re-fetch via `getJiraIssue` if needed
- [ ] Present implementation brief — AC per ticket
- [ ] Read CLAUDE.md / project instructions for coding conventions
- [ ] Read any spec files referenced in ticket descriptions (SCHEMA.md, API.md, SCREENS.md, mockups)
- [ ] Implement each ticket following project conventions
- [ ] For multiple tickets (standalone) — check dependencies, implement in order
- [ ] Run tests if test infrastructure exists
- [ ] Run linter if configured
- [ ] After each ticket's implementation → offer to transition to done/review
  - Standalone: use done transition ID from Step 2
  - Sprint mode: fetch transitions via `getTransitionsForJiraIssue` if needed

---

## Edge Cases Checklist

- [ ] Ticket already in target status → note it, skip transition
- [ ] Ticket in post-implementation status (In Review, Done, Closed) → flag it, ask user
- [ ] Permission error on transition → report, suggest manual transition
- [ ] Transition call returns error → report specific error, offer retry
- [ ] Multiple Jira sites → ask user which to use (standalone only)
- [ ] Sprint-level command → redirect to `/implement-sprint`

---

## Quick Reference: Supported Issue Types

| Type | Supported | Action if Encountered |
|------|-----------|----------------------|
| Story | Yes | Process normally |
| Task | Yes | Process normally |
| Sub-task | Yes | Process normally |
| Epic | No | Skip, offer to list child tickets |
| Bug | No | Skip, explain scope |
| Other | No | Skip, explain scope |

---

## Quick Reference: Mode Comparison

| Step | Standalone | Sprint Mode |
|------|-----------|-------------|
| Pre-flight | Full discovery | Skipped (cloudId known) |
| Step 0: Identify | Parse user message | Skipped (ticket key passed) |
| Step 1: Fetch details | `getJiraIssue` | Skipped (context available) |
| Step 2: Transitions | `getTransitionsForJiraIssue` | Skipped (already discovered) |
| Step 3: Confirm | Present table, wait | Skipped (sprint plan confirmed) |
| Step 4: Execute | Transition + assign | Skipped (already done) |
| Step 5: Implement | Full implementation | **Full implementation** |
| Post-impl transition | Use Step 2 IDs | Re-fetch if needed |
