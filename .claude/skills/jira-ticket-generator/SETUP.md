# JIRA Ticket Generator — Setup Guide

Reads module specification folders and generates import-ready JIRA tickets with epics, stories, sub-tasks, estimates, dependencies, labels, and sprint suggestions.

---

## Setup

### Claude Code
```bash
cp -r jira-ticket-generator/ ~/.claude/skills/
```

### Claude.ai Project
1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload all 3 reference files as knowledge

---

## Usage

### Generate all tickets
```
"Read all module folders in modules/ and generate JIRA tickets for every module. Output as markdown in tickets/ folder."
```

### Single module
```
"Generate JIRA tickets for module 05-allocation-tracking"
```

### Single phase
```
"Generate JIRA tickets for all Phase 1 modules only"
```

### CSV for JIRA import
```
"Generate JIRA tickets for all modules as a single CSV file for JIRA import"
```

### With sprint plan
```
"Generate JIRA tickets for Phase 1 with sprint suggestions for 1 developer"
```

---

## Output

### Markdown (per module)
```
tickets/
├── 01-auth-and-roles.md
├── 02-client-management.md
├── 03-project-management.md
├── ...
└── SPRINT-PLAN.md
```

### CSV (single file)
```
tickets/
└── jira-import.csv        ← Upload directly to JIRA
```

---

## Pipeline Position

```
PRD Brainstorm → FSD Generator → Repo Architect → JIRA Ticket Generator
                                                   ↑ You are here
```

The Repo Architect creates module folders. This agent reads them and produces tickets.

---

## File Inventory

| File | Purpose |
|------|---------|
| `SKILL.md` | Core agent instructions |
| `claude-ai-project-prompt.md` | System prompt for Claude.ai |
| `references/story-patterns.md` | Story breakdown patterns per module type (5 patterns) |
| `references/estimation-guide.md` | Sizing framework with examples |
| `references/csv-format.md` | JIRA CSV import column mapping and format |
