# Implement Ticket — Setup Guide

Pre-implementation gate that updates JIRA ticket statuses before coding begins. Fetches ticket details and available transitions from Jira, confirms status changes with the user, optionally assigns tickets, transitions them, and hands off to implementation.

Supports **stories, tasks, and sub-tasks**. Works with any Jira workflow — discovers available statuses at runtime.

---

## Install

### Claude Code

```bash
cp -r implement-ticket/ ~/.claude/skills/
```

### Claude.ai Project

1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload `references/workflow-checklist.md` as knowledge

---

## Jira MCP Setup (Required)

This skill requires the Atlassian MCP for Jira integration. Set it up with:

```bash
claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
```

On first use, you'll be prompted to authenticate via OAuth with your Atlassian account.

### Required Permissions

Your Jira account needs:
- **Browse projects** — to read ticket details
- **Transition issues** — to change ticket statuses
- **Assign issues** — to assign tickets (optional, only if you use the assignment feature)
- **Edit issues** — to update the assignee field

---

## Trigger Phrases

The skill activates on any of these (or similar):

- "implement PROJ-123"
- "start working on PROJ-123"
- "pick up PROJ-123"
- "work on ticket PROJ-123"
- "implement PROJ-123, PROJ-124, PROJ-125"
- "start these tickets: PROJ-100, PROJ-101"
- "I want to work on PROJ-123"
- Any request to begin implementing a specific JIRA ticket

---

## Usage Examples

### Single ticket

```
"Implement PROJ-123"
```
→ Fetches PROJ-123 from Jira → shows current status and proposed transition → you confirm → status updated → reads ticket description and AC → starts implementation

### Multiple tickets

```
"Start working on PROJ-123, PROJ-124, and PROJ-125"
```
→ Fetches all three → presents consolidated table of status changes → you confirm once → all transitioned → implements in dependency order

### With assignment

```
"Pick up PROJ-200"
```
→ Fetches ticket → sees it's unassigned → asks if you want it assigned to you → you confirm → transitions + assigns → starts implementation

### Already in progress

```
"Implement PROJ-300"
```
→ Fetches ticket → sees it's already "In Progress" → skips transition → goes straight to implementation

---

## How It Works

```
Step 0: Extract ticket keys from your message
   ↓
Step 1: Fetch ticket details from Jira (type, status, assignee)
   ↓  (filter: stories/tasks/sub-tasks only)
Step 2: Fetch available transitions per ticket
   ↓
Step 3: Present confirmation table  ← gate: user confirmation
   ↓
Step 4: Execute transitions + optional assignment
   ↓
Step 5: Hand off to implementation (read ticket → build → test → offer done transition)
```

---

## File Inventory

| File | Purpose |
|---|---|
| `SKILL.md` | Core skill instructions for Claude Code |
| `claude-ai-project-prompt.md` | Condensed system prompt for Claude.ai |
| `SETUP.md` | This file — installation and usage guide |
| `references/workflow-checklist.md` | Runtime checklist read at every invocation to ensure no step is skipped |
