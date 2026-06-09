# FSD Generator Agent — Setup Guide

This agent reads a PRD and generates a comprehensive FSD (Functional Specification Document) with entity definitions, state machines, calculations, validations, ER diagrams, DFDs, edge cases, and a phase-wise implementation guide.

---

## Option 1: Claude.ai Project (Recommended)

### Setup Steps

1. **Create a new Project** in Claude.ai

2. **Paste the System Prompt**: Copy `claude-ai-project-prompt.md` into the Project's custom instructions.

3. **Upload Knowledge Files** to the Project:
   - `references/fsd-structure.md` — Section pool and formatting guidance
   - `references/gap-analysis.md` — Comprehensive gap checklist for PRD→FSD translation
   - `references/entity-patterns.md` — Common patterns, naming conventions, type standards
   - `assets/fsd-html-template.html` — Base HTML template for interactive FSD output

4. **Enable Tools**:
   - File Creation (for .docx and .html output)
   - Web Search (optional — for researching implementation patterns)

### How a Session Works

1. Upload or paste a PRD
2. The agent reads it and identifies entities, relationships, workflows, and gaps
3. It asks 2-3 implementation-specific clarification questions
4. After your answers, it generates the FSD in your preferred format (HTML, Word, or both)

### Tips

- **Upload the PRD as a file** rather than pasting — it preserves structure and formatting.
- **Tell the agent the output format upfront**: "Read this PRD and generate an FSD as interactive HTML."
- **Review the gap questions carefully** — they often surface edge cases the PRD missed.
- **The phase guide is the most implementation-critical section** — verify entity/field assignments match your team's capacity.

---

## Option 2: Claude Code (Skill)

### Setup Steps

1. Copy the skill directory to your Claude Code skills location:
   ```bash
   cp -r fsd-generator/ ~/.claude/skills/fsd-generator/
   ```

2. Verify structure:
   ```
   fsd-generator/
   ├── SKILL.md
   ├── references/
   │   ├── fsd-structure.md
   │   ├── gap-analysis.md
   │   └── entity-patterns.md
   ├── assets/
   │   └── fsd-html-template.html
   ├── claude-ai-project-prompt.md
   └── SETUP.md
   ```

3. Use it: Place a PRD file in your working directory and ask Claude Code to generate an FSD from it.

---

## What the Agent Produces

### During the Conversation
- Structured identification of entities, relationships, and workflows from the PRD
- Gap analysis questions (implementation details the PRD doesn't specify)
- Architectural decisions with documented rationale

### Final Output
- **Interactive HTML**: Sidebar nav, collapsible entity panels, mermaid.js ER diagram, SVG DFD, state machine visuals, formula blocks, phase timeline. Best for screen review.
- **Word Document (.docx)**: Professional formatting, embedded ER/DFD as images, entity tables, sign-off section. Best for formal approval.
- **Both**: Identical content, two formats.

---

## Chaining with PRD Brainstorm Agent

These two agents work as a pipeline:

1. **PRD Brainstorm Agent** → produces PRD (v1.0, v1.1, etc.)
2. **FSD Generator Agent** → reads the PRD, produces FSD

You can run them in sequence within the same Claude.ai Project, or as separate conversations. The FSD agent accepts any PRD format — it doesn't need to come from the brainstorm agent specifically.

---

## File Inventory

| File | Purpose |
|------|---------|
| `SKILL.md` | Core agent instructions (Claude Code) |
| `claude-ai-project-prompt.md` | System prompt for Claude.ai Projects |
| `references/fsd-structure.md` | Section pool, formatting rules, quality checklist |
| `references/gap-analysis.md` | Comprehensive PRD gap checklist (11 categories, 80+ checks) |
| `references/entity-patterns.md` | Entity templates, naming conventions, type standards, anti-patterns |
| `assets/fsd-html-template.html` | Base HTML template for interactive FSD output |
| `SETUP.md` | This file |
