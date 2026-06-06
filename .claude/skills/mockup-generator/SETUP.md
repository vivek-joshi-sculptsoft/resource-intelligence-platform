# Mockup Generator — Setup Guide

Reads SCREENS.md from module folders and generates interactive HTML mockups with realistic data, role-based view switching, and responsive layouts.

---

## Setup

### Claude Code
```bash
cp -r mockup-generator/ ~/.claude/skills/
```

### Claude.ai Project
1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload: `references/design-tokens.md`, `references/component-library.md`
3. Enable File Creation

---

## Usage

```bash
# Single module
claude "Generate mockups for module 05-allocation-tracking"

# Specific screen
claude "Mock up the Resource Availability View from module 10"

# All modules
claude "Generate mockups for all modules"

# Role comparison
claude "Show me Project Detail View as PM vs Engineer"
```

---

## Output

```
modules/{module}/mockups/
├── screen-name.html       ← Open directly in browser
├── screen-form.html
└── ...
```

Each file is self-contained. No build step. Double-click to open.

---

## Pipeline Position

```
PRD Brainstorm → FSD Generator → Repo Architect → JIRA Tickets
                                       ↓
                                 Mockup Generator
```

Runs after Repo Architect creates module folders with SCREENS.md.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Core instructions |
| `claude-ai-project-prompt.md` | System prompt for Claude.ai |
| `references/design-tokens.md` | Complete CSS design system |
| `references/component-library.md` | Reusable HTML/CSS/JS component patterns |
