# Implement Ticket — Runtime Workflow Checklist

Read this at the start of every invocation. Use it as a live checklist to ensure no step is skipped.

---

## Pre-Flight

- [ ] Check for Jira MCP tools (tool names containing `atlassian` or `jira`)
  - If not available → tell user to set up Atlassian MCP, STOP
- [ ] Discover cloudId — call `getAccessibleAtlassianResources`
  - One site → use it
  - Multiple sites → ask user
  - Cache for session

---

## Step 0: Identify Tickets

- [ ] Extract ticket keys from user message (pattern: `{PROJECT}-{NUMBER}`)
- [ ] If no keys found → ask user for specific ticket key(s)
- [ ] If multiple keys → collect all, process as batch

---

## Step 1: Fetch Ticket Details

For each ticket key:
- [ ] Call `getJiraIssue` — collect: key, summary, type, status, assignee
- [ ] Filter by type — only stories, tasks, sub-tasks
  - Epic or bug → flag it, skip it, offer to list child tickets
- [ ] If ALL tickets filtered out → STOP

---

## Step 2: Fetch Available Transitions

For each valid ticket:
- [ ] Call `getTransitionsForJiraIssue`
- [ ] Identify the most likely "start work" transition (names containing: in progress, in development, start, begin, active, working)
- [ ] If multiple candidates → present all options to user
- [ ] If no transitions returned or call fails → ask user for target status name

---

## Step 3: Present Confirmation

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

## Step 4: Execute Transitions

For each confirmed ticket:
- [ ] Call `transitionJiraIssue` with confirmed transition ID
- [ ] If assignment requested → call `editJiraIssue` to set assignee field
- [ ] Report success/failure per ticket
- [ ] If any fail → report error, ask retry or skip

---

## Step 5: Hand Off to Implementation

- [ ] Read each ticket's full description and acceptance criteria (from Step 1 data)
- [ ] Present implementation brief — description + AC per ticket
- [ ] Read CLAUDE.md / project instructions for coding conventions
- [ ] Read any spec files referenced in ticket descriptions
- [ ] Implement each ticket following project conventions
- [ ] For multiple tickets — check dependencies, implement in order
- [ ] Run tests if test infrastructure exists
- [ ] Run linter if configured
- [ ] After each ticket's implementation → ask user about transitioning to done/review

---

## Edge Cases Checklist

- [ ] Ticket already in target status → note it, skip transition
- [ ] Ticket in post-implementation status (In Review, Done, Closed) → flag it, ask user
- [ ] Permission error on transition → report, suggest manual transition
- [ ] Transition call returns error → report specific error, offer retry
- [ ] Multiple Jira sites → ask user which to use (Step 0)

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
