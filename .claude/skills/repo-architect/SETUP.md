# Repo Architect Agent — Setup Guide

This agent reads a PRD and FSD from a git repo and automatically generates the complete module-wise project structure — shared references, module specs, JIRA tickets, CLAUDE.md, and roadmap.

---

## Prerequisites

Your repo must have:
```
project/
├── prd/
│   └── PRD.md
├── fsd/
│   └── FSD.md
```

That's it. Everything else is generated.

---

## Option 1: Claude Code (Recommended)

### Setup
1. Copy the skill:
   ```bash
   cp -r repo-architect/ ~/.claude/skills/repo-architect/
   ```

2. Navigate to your project repo:
   ```bash
   cd your-project/
   ```

3. Run:
   ```bash
   claude "Read prd/PRD.md and fsd/FSD.md, then generate the complete module-wise repo structure using the repo-architect skill"
   ```

### What Happens
Claude Code reads both documents, identifies modules, determines build order, and creates ~70+ files:
- 4 shared reference files
- 5 files × N modules (typically 10-15 modules)
- N ticket files
- CLAUDE.md, ROADMAP.md, README.md

---

## Option 2: Claude.ai Project

### Setup
1. Create a new Project
2. Paste `claude-ai-project-prompt.md` as custom instructions
3. Upload knowledge files: `references/module-templates.md`, `references/claude-md-template.md`, `references/ticket-patterns.md`
4. Enable File Creation

### Usage
Upload your PRD.md and FSD.md, then say: "Generate the complete module-wise repo structure from these documents."

Download the generated files and place them in your repo.

---

## Pipeline: Full Workflow

These three agents chain together:

```
1. PRD Brainstorm Agent  → produces PRD.md
2. FSD Generator Agent   → reads PRD.md, produces FSD.md
3. Repo Architect Agent  → reads both, generates full repo structure
```

After the pipeline:
```
4. Decide tech stack → update CLAUDE.md
5. Claude Code builds module by module
```

---

## File Inventory

| File | Purpose |
|------|---------|
| `SKILL.md` | Core agent instructions (Claude Code) |
| `claude-ai-project-prompt.md` | System prompt for Claude.ai Projects |
| `references/module-templates.md` | Templates for all 5 module files |
| `references/claude-md-template.md` | Template for CLAUDE.md generation |
| `references/ticket-patterns.md` | JIRA story breakdown patterns |
| `SETUP.md` | This file |
