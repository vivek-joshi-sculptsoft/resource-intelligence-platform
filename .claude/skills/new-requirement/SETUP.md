# New Requirement — Setup Guide

Enforces a strict gated workflow whenever you describe a new requirement, change request, or feature addition. Analyzes the requirement, updates your documentation/spec files, creates tickets, asks whether to implement now, and optionally builds the code — all in sequence, with gates between each step.

Works with **any project type** — web apps, CLI tools, libraries, data pipelines, mobile apps, microservices, monorepos, single scripts. Discovers your project's conventions at runtime. Never assumes a tech stack, folder structure, or issue tracker.

---

## Install

### Claude Code

```bash
cp -r new-requirement/ ~/.claude/skills/
```

### Claude.ai Project

1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload `references/workflow-checklist.md` as knowledge

---

## Issue Tracker Integration (Optional)

The skill works without any issue tracker — it creates local markdown ticket files as fallback. For direct integration, connect one of:

| Tracker | Setup |
|---|---|
| **Jira (Atlassian)** | `claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v1/mcp` |
| **Linear** | Connect Linear MCP per Linear's developer docs |
| **GitHub Issues** | Available via Claude Code's built-in GitHub integration |
| **GitLab** | Connect GitLab MCP per GitLab's developer docs |
| **Others** | Any MCP that exposes create/update issue tools will be detected automatically |

The skill detects which tracker is connected at runtime by scanning available MCP tool names. No configuration needed — connect the MCP and the skill adapts.

---

## How It Works

### Project Discovery (Phase 0)

On first invocation per session, the skill builds a profile of your project:

- Reads CLAUDE.md / README.md / project instructions
- Identifies project type (CLI, web app, library, pipeline, etc.)
- Finds your documentation and spec files (if any)
- Finds your ticket and task files (if any)
- Detects available issue tracker MCP
- Detects your methodology (sprint-based, Kanban, or none)
- Detects test framework, linter, CI/CD, changelog
- Sets formality level based on what it finds

This is cached for the session — subsequent requirements in the same session skip Phase 0.

### The 5 Phases

```
Phase 0: Project Discovery (once per session)
   ↓
Phase 1: Analyze & Classify  ← gate: user confirmation
   ↓
Phase 2: Update Docs/Specs   ← gate: user confirmation
   ↓
Phase 3: Create Tickets      ← flows continuously
   ↓
Phase 4: Scheduling Decision ← gate: user picks a/b/c
   ↓ (only if user picks "implement now")
Phase 5: Implement
```

### Formality Levels

| Level | When | Behavior |
|---|---|---|
| **Full** | Project has spec files + issue tracker + test suite | All phases, all gates, full detail |
| **Standard** | Project has some of the above | All phases, skip what's missing |
| **Lightweight** | Single-file project, no specs, no tracker, no tests | Phases 1-3 compressed into one confirmation |

### Graceful Degradation

| Missing | What happens |
|---|---|
| No spec/doc system | Skips Phase 2 (or sets one up if you ask) |
| No issue tracker MCP | Creates local markdown ticket files |
| No test infrastructure | Asks before adding any |
| No linter | Skips lint step |
| No CLAUDE.md | Asks about conventions before implementing |
| No codebase yet | After tickets, asks: scaffold project or stop? |
| Multi-repo requirement | Identifies affected repos, tracks per-repo in tickets |

---

## Trigger Phrases

The skill activates on any of these (or similar):

- "new requirement: ..."
- "add feature: ..."
- "change request: ..."
- "I need to add ..."
- "we need a new ..."
- "add this capability: ..."
- "add a `--dry-run` flag ..."
- "support X in ..."
- "we need to handle ..."
- Any description of new functionality that doesn't currently exist

---

## Usage Examples

### Web App
```
"New requirement: users should be able to set notification preferences — email, push, and in-app, per event type"
```
→ Phase 0 discovers your modules, DB schema, API spec files, Jira connection, and sprint setup
→ Phase 1 classifies as NEW_COMPONENT, identifies affected REQUIREMENTS.md, SCHEMA.md, API.md
→ Phase 2 updates those spec files following your existing format
→ Phase 3 creates Jira story under the correct epic
→ Phase 4 asks about scheduling
→ Phase 5 (if chosen) builds the feature following your CLAUDE.md conventions

### CLI Tool
```
"Add a `--dry-run` flag to the deploy command that prints what would happen without making any changes"
```
→ Lightweight project → Phase 0 detects no spec system → compresses to one confirmation
→ Creates a local ticket, asks about implementation
→ Implements the flag in the correct command handler

### Data Pipeline
```
"We need a new data source connector for Salesforce — pull Opportunities and Accounts on a daily schedule"
```
→ Detects Airflow/Prefect DAG structure, finds connector patterns in existing DAGs
→ Updates pipeline docs/spec following existing connector format
→ Creates Linear issue
→ Builds DAG + operator following existing connector patterns

### Library
```
"Add a `.groupBy()` method to the Collection class — similar to Lodash groupBy"
```
→ Detects library project, finds exported API surface
→ Updates type definitions and API docs
→ Creates GitHub Issue
→ Implements method + tests following existing test patterns

### Microservices
```
"Change request: support multi-region failover in the auth service — primary US-East, failover US-West"
```
→ Detects multi-service setup, identifies auth service scope
→ Updates service spec and architecture docs
→ Creates Jira story with cross-service dependency notes
→ Implements with region config + failover logic

---

## File Inventory

| File | Purpose |
|---|---|
| `SKILL.md` | Core skill instructions for Claude Code |
| `claude-ai-project-prompt.md` | Condensed system prompt for Claude.ai |
| `references/workflow-checklist.md` | Runtime checklist — read at every invocation to ensure no step is skipped |
