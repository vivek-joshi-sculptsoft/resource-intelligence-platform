# Implement Sprint — Setup Guide

Sprint-level orchestrator that fetches all tickets from a Jira sprint and implements them sequentially using the `/implement-ticket` skill. Handles sprint discovery, dependency-aware ordering, progress tracking, and per-ticket delegation.

Supports **stories, tasks, and sub-tasks**. Skips epics and bugs.

---

## Prerequisites

This skill requires the **implement-ticket** skill to be installed. It delegates each ticket's status transitions, confirmation, and implementation to `/implement-ticket`.

---

## Install

### Claude Code

```bash
cp -r implement-sprint/ ~/.claude/skills/
cp -r implement-ticket/ ~/.claude/skills/   # required dependency
```

### Claude.ai Project

1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload `references/workflow-checklist.md` as knowledge
3. Also set up the implement-ticket skill in the same project (required dependency)

---

## Jira MCP Setup (Required)

This skill requires the Atlassian MCP for Jira integration. Set it up with:

```bash
claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
```

On first use, you'll be prompted to authenticate via OAuth with your Atlassian account.

### Required Permissions

Your Jira account needs:
- **Browse projects** — to read sprint and ticket details
- **Transition issues** — to change ticket statuses (via /implement-ticket)
- **Assign issues** — to assign tickets (optional, via /implement-ticket)
- **Edit issues** — to update the assignee field (via /implement-ticket)

---

## Trigger Phrases

The skill activates on any of these (or similar):

- "implement sprint 3"
- "execute sprint 2"
- "start sprint 1"
- "run sprint 4"
- "kick off sprint 3"
- "begin sprint 1"
- "implement the current sprint"
- "implement active sprint"
- "implement sprint Auth-Foundation"
- "continue sprint 3" (resume mid-sprint)
- Any request to implement all tickets in a sprint

---

## Usage Examples

### By sprint number

```
"Implement sprint 3"
```
→ Finds Sprint 3 in Jira → fetches all tickets → presents ordered plan → you confirm → implements each ticket via /implement-ticket sequentially

### By sprint name

```
"Implement sprint Auth-Foundation"
```
→ Searches for sprint by name → same flow

### Current/active sprint

```
"Implement the current sprint"
```
→ Finds the active sprint → same flow

### Resume mid-sprint

```
"Continue sprint 3"
```
→ Fetches Sprint 3 tickets → detects which are already done → starts from first non-done ticket

### Subset selection

```
"Implement sprint 3, just the backend tickets"
```
→ Fetches all tickets → presents plan → you select subset → implements only selected tickets

---

## How It Works

```
Step 0: Discover Jira Cloud ID
   ↓
Step 1: Identify the sprint (number, name, or active)
   ↓
Step 2: Fetch all tickets in the sprint from Jira
   ↓  (filter: stories/tasks/sub-tasks only)
Step 3: Determine implementation order (dependency-aware)
   ↓
Step 4: Present sprint plan  ← gate: user confirmation
   ↓
Step 5: For each ticket:
   ├── Show progress header
   ├── Invoke /implement-ticket  ← delegates transitions + implementation
   ├── Show updated progress
   └── Ask continue / pause / skip
   ↓
Step 6: Sprint completion summary
```

---

## File Inventory

| File | Purpose |
|---|---|
| `SKILL.md` | Core skill instructions for Claude Code |
| `claude-ai-project-prompt.md` | Condensed system prompt for Claude.ai |
| `SETUP.md` | This file — installation and usage guide |
| `references/workflow-checklist.md` | Runtime checklist read at every invocation to ensure no step is skipped |
