# Implement Sprint — Runtime Workflow Checklist

Read this at the start of every invocation. Use it as a live checklist to ensure no step is skipped.

---

## Pre-Flight

- [ ] Check for Jira MCP tools (tool names containing `atlassian` or `jira`)
  - If not available → tell user to set up Atlassian MCP, STOP
- [ ] Check that `/implement-ticket` skill is available
  - If not available → tell user to install the implement-ticket skill, STOP
- [ ] Discover cloudId — call `getAccessibleAtlassianResources`
  - One site → use it
  - Multiple sites → ask user
  - Cache for session

---

## Step 1: Identify the Sprint

- [ ] Parse user message for sprint identifier
  - Sprint number → search JQL: `sprint = "Sprint N"`
  - Sprint name → search JQL: `sprint = "{name}"`
  - "Current" / "active" → `sprint in openSprints() AND project = {PROJECT}`
  - No identifier → ask user
- [ ] If project key unknown → ask user
- [ ] If multiple sprints match → present choices, ask user
- [ ] If no sprint found → report, ask for clarification

---

## Step 2: Fetch All Sprint Tickets

- [ ] Query: `sprint = "{sprint}" ORDER BY rank ASC`
- [ ] Collect per ticket: key, summary, issue type, status, assignee, priority
- [ ] Filter by type — only stories, tasks, sub-tasks
  - Epic or bug → flag it, skip it
- [ ] If ALL tickets filtered out → STOP
- [ ] Count: total, filtered, already-done

---

## Step 3: Discover Ticket Workflows ← WORKFLOW-FIRST GATE

**This step MUST complete before any status changes are planned or presented.**

For each ticket:
- [ ] Call `getTransitionsForJiraIssue` to get available transitions from current status
- [ ] Record current status (from Step 2)
- [ ] Record all available transitions (names + IDs)
- [ ] Identify start-work transition — names containing (case-insensitive):
  `in progress`, `in development`, `start`, `begin`, `active`, `working`
- [ ] Identify done/review transition — names containing:
  `done`, `review`, `resolved`, `closed`, `complete`
- [ ] Classify each ticket's workflow readiness:

| Classification | Condition | Action |
|---------------|-----------|--------|
| Ready | Has valid start-work transition | Proceed normally |
| Already started | Current status is an in-progress state | Skip start transition |
| Already done | Current status is done/closed/resolved | Skip entirely |
| Workflow blocked | No valid start-work transition | Flag for user |
| Multiple candidates | >1 plausible start transition | Present options |
| Fetch failed | API error / permissions | Flag, defer to /implement-ticket |

- [ ] If different tickets have different workflows → note workflow groups
- [ ] If any tickets are workflow-blocked → prepare user-facing warnings
- [ ] If any tickets have multiple candidates → prepare user choice prompt

---

## Step 4: Determine Implementation Order

- [ ] Fetch issue links for each ticket (`getJiraIssue` — look at issuelinks)
- [ ] Build dependency graph from blocked-by / depends-on links
- [ ] Check for circular dependencies
  - Circular → flag, fall back to Jira rank order
- [ ] Topologically sort — prerequisites first
- [ ] If no explicit dependencies → order by type heuristic:
  1. Infrastructure / config
  2. Data model / schema
  3. Backend / API
  4. Frontend / UI
  5. Integration / glue
- [ ] Within same category → preserve Jira rank order

---

## Step 5: Present Sprint Plan

- [ ] Show workflow summary — discovered start and done transitions
  - If different workflows exist → show per-ticket transitions
- [ ] Build ordered table: #, Ticket, Title, Type, Current Status, → Start Transition, Depends On
- [ ] Note already-done tickets
- [ ] Flag workflow-blocked tickets with ⚠
- [ ] Resolve multiple-candidate transitions with user
- [ ] If sprint has >15 tickets → warn about session length
- [ ] Present plan with options:
  - a) Start from ticket #1
  - b) Start from first non-done ticket
  - c) Pick specific tickets
  - d) Change order
- [ ] **WAIT FOR USER CONFIRMATION**
- [ ] If user picks subset → re-present filtered list for confirmation
- [ ] If user reorders → re-present for confirmation

---

## Step 6: Sequential Implementation

For each ticket in confirmed order:

- [ ] Show progress header with workflow path: `{current} → {start_transition} → ... → {done_transition}`
- [ ] Invoke `/implement-ticket` with the ticket key + discovered workflow context
  - /implement-ticket handles: confirm status change using discovered transitions, transition, implement, offer done/review transition
- [ ] After /implement-ticket completes → re-fetch ticket status from Jira to verify transition
- [ ] Show sprint progress table with verified statuses
- [ ] Ask user: continue (y) / pause (n) / skip
  - y → proceed to next ticket
  - n → pause sprint, inform user they can resume with "continue sprint"
  - skip → mark as skipped, proceed to next
- [ ] Ensure changes are committed before moving to next ticket

---

## Step 7: Sprint Completion

- [ ] Show final summary table: #, Ticket, Title, Start Status, Final Status, Result
- [ ] Report counts: implemented, skipped, failed
- [ ] Sprint complete

---

## Edge Cases Checklist

### Workflow Edge Cases
- [ ] No valid start-work transition → present all available transitions, ask user to pick
- [ ] Different workflows across tickets → group by workflow, show per-ticket transitions
- [ ] Transition available in Step 3 but fails in Step 6 → re-fetch transitions, report change
- [ ] Empty transitions list (permissions) → flag, ask proceed without status change or skip
- [ ] Transition names don't match any pattern → present full list, ask user

### General Edge Cases
- [ ] Ticket already done (Done/Closed/Resolved) → skip automatically, note in progress
- [ ] Ticket in progress by someone else → flag, ask implement or skip
- [ ] Sprint has no tickets → inform user, suggest different sprint
- [ ] All tickets are epics/bugs → STOP with explanation
- [ ] Mid-sprint resume ("continue sprint") → detect done tickets, start from first non-done
- [ ] Implementation failure or user aborts mid-ticket → offer retry / skip / pause
- [ ] Large sprint (>15 tickets) → warn, offer subset
- [ ] Circular dependencies → flag, fall back to rank order
- [ ] Multiple Jira sites → ask user which to use (Step 0)

---

## Quick Reference: /implement-ticket Delegation

This skill does NOT handle these — /implement-ticket does:

| Concern | Handled By |
|---------|-----------|
| Confirming status change per ticket | /implement-ticket Step 3 |
| Executing transitions | /implement-ticket Step 4 |
| Assigning tickets | /implement-ticket Step 4 |
| Reading specs and implementing | /implement-ticket Step 5 |
| Offering done/review transition | /implement-ticket Step 5 |

This skill handles (and passes context to /implement-ticket):

| Concern | Step |
|---------|------|
| Sprint discovery | Step 1 |
| Fetching all sprint tickets | Step 2 |
| **Discovering ticket workflows** | **Step 3** |
| Dependency ordering | Step 4 |
| Sprint plan with workflow info | Step 5 |
| Progress tracking with verified statuses | Step 6 |
| Flow control (continue/pause/skip) | Step 6 |
| Sprint completion summary | Step 7 |
