# JIRA Ticket Generator — Setup Guide

Reads module specification folders and generates import-ready JIRA tickets with epics, stories, sub-tasks, estimates, dependencies, labels, and sprint suggestions. Integrates with Jira via MCP to create tickets directly when available.

---

## Setup

### Claude Code
```bash
cp -r jira-ticket-generator/ ~/.claude/skills/
```

### Claude.ai Project
1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload all 4 reference files as knowledge

---

## Jira MCP Setup (for direct Jira creation)

The skill uses the **official Atlassian Remote MCP** — GA since February 2026, OAuth-based, no local install required.

### Connect Atlassian MCP to Claude Code

```bash
claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp
```

On first use, Claude Code opens a browser OAuth flow to authenticate with your Atlassian account. The connection persists after that — no re-auth needed per session.

**What it supports:** Jira Cloud, Confluence, Compass. Full read/write: create issues, link issues (blocked-by), update sprint assignments, manage epics.

> For the latest setup URL and OAuth flow details, refer to [Atlassian's official MCP documentation](https://developer.atlassian.com/cloud/jira/platform/mcp/).

### Required Atlassian Permissions

The authenticated Atlassian account must have:
- `Create Issues` on the target Jira project
- `Edit Issues` (for setting dependencies and sprint fields)
- `Browse Projects`

### Pre-Creation Checklist
Before running the skill in Jira MCP mode:
- [ ] Atlassian MCP connected and authenticated (`claude mcp list` should show `atlassian`)
- [ ] Jira project created with issue types: Epic, Story, Sub-task, Task
- [ ] Custom field "Story Points" enabled (or equivalent estimate field)
- [ ] Board configured with active sprints (optional — skill suggests sprints without them)

---

## Usage

### Direct Jira creation (recommended)
```
"Generate JIRA tickets for all modules and create them in Jira. Project key: MYPROJ"
```

### With distribution preferences
```
"Create stories in Jira for module 05-allocation-tracking. I want one epic per module and my team is FE/BE split."
```

### Generate user stories only, technical tasks later
```
"Create user stories in Jira for all Phase 1 modules."
# ... review stories ...
"Now break the L and XL stories into technical tasks."
```

### File output only
```
"Generate JIRA tickets for all modules as markdown files."
```

### Single module
```
"Generate JIRA tickets for module 05-allocation-tracking"
```

### Single phase
```
"Generate JIRA tickets for all Phase 1 modules only"
```

### CSV for manual JIRA import
```
"Generate JIRA tickets for all modules as a single CSV file for JIRA import"
```

### With sprint plan
```
"Generate JIRA tickets for Phase 1 with sprint suggestions for 1 developer"
```

---

## Preference Questions

When creating in Jira, the skill asks 5 questions before starting:

| # | Question | Default Recommendation |
|---|---|---|
| 1 | Epic grouping strategy | One epic per module |
| 2 | Story granularity | Medium (2-3 days) |
| 3 | Team structure | Full-stack |
| 4 | Technical task split pattern | FE + BE tasks for L/XL |
| 5 | Sprint length and velocity | 2-week / 20 pts per dev |

You can answer all 5 at once: `"a, b, a, b, b"` — the skill maps them in order.

---

## Two-Phase Creation

**Phase 1** — Always runs first. Creates Epics and User Stories in Jira.

**Phase 2** — Runs only when you ask. Breaks stories into technical sub-tasks.

Trigger Phase 2 with any of:
- "break into tasks"
- "create technical tasks"
- "add sub-tasks"
- "distribute technical work"
- "create BE/FE tasks"

---

## Output

### File output (markdown, per module)
```
tickets/
├── 01-auth-and-roles.md
├── 02-client-management.md
├── 03-project-management.md
├── ...
└── SPRINT-PLAN.md
```

### File output (CSV)
```
tickets/
└── jira-import.csv        ← Upload directly to JIRA
```

### Jira MCP output
Post-creation summary report printed in conversation:
- Epics created with Jira keys
- Stories created with Jira keys, sprint assignments, story points
- Sub-tasks created (if Phase 2 ran)
- Any failed tickets with retry/export option

---

## Pipeline Position

```
PRD Brainstorm → FSD Generator → Repo Architect → JIRA Ticket Generator
                                                   ↑ You are here
```

The Repo Architect creates module folders. This skill reads them and produces tickets (as files or directly in Jira).

---

## File Inventory

| File | Purpose |
|------|---------|
| `SKILL.md` | Core skill instructions for Claude Code |
| `claude-ai-project-prompt.md` | Condensed system prompt for Claude.ai |
| `references/jira-mcp-guide.md` | Preference questionnaire, epic/story/task distribution standards, MCP creation sequence |
| `references/story-patterns.md` | Story breakdown patterns per module type (5 patterns) |
| `references/estimation-guide.md` | Sizing framework with examples |
| `references/csv-format.md` | JIRA CSV import column mapping and format |
