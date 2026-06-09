# PRD Brainstorm Agent — Setup Guide

This agent conducts interactive product requirement brainstorming sessions and produces professional PRDs. It works across two environments.

---

## Option 1: Claude.ai Project (Recommended for Team Use)

Best for: Teams who want a shared, reusable brainstorming space with web search and file creation built in.

### Setup Steps

1. **Create a new Project** in Claude.ai (Settings → Projects → New Project)

2. **Set the Project Name**: "PRD Brainstorm" (or whatever you prefer)

3. **Paste the System Prompt**: Copy the full contents of `claude-ai-project-prompt.md` into the Project's custom instructions field.

4. **Upload Knowledge Files** (optional but recommended): Upload these reference files to the Project's knowledge base. Claude will read them as needed during conversations:
   - `references/conversation-framework.md` — Domain detection signals and question patterns
   - `references/research-playbook.md` — Competitor analysis and feasibility frameworks
   - `references/prd-structure.md` — PRD template and section guidance
   - `assets/prd-html-template.html` — HTML template for interactive PRD output

5. **Enable Tools**: Make sure these are enabled for the project:
   - Web Search (for competitor research and feasibility checks)
   - File Creation (for generating .docx and .html PRD outputs)

6. **Start a Conversation**: Open the project and describe what you want to build. The agent will guide the session from there.

### How a Session Works

- Start by describing the system/product you want to build
- The agent asks layered questions (2-3 per exchange)
- You answer, the agent digs deeper based on your responses
- If competitors or alternatives are relevant, the agent researches them
- When enough is gathered, the agent presents a structured consolidation for your review
- After your confirmation, it generates the PRD in your preferred format

### Tips for Best Results

- **Don't pre-structure your input.** Just describe the problem naturally. "We're an IT services company and we're drowning in spreadsheets tracking who's on what project" is a perfect starting message.
- **Push back on the agent.** If it suggests something you don't need, say so. If a question doesn't make sense for your context, tell it why.
- **Ask it to research.** "Are there tools that already do this?" or "Is this technically feasible?" will trigger the research phase.
- **Review the consolidation carefully.** This is your checkpoint before the PRD is generated. Add, remove, or adjust anything.

---

## Option 2: Claude Code (Skill)

Best for: Developers or solo practitioners who prefer terminal-based workflows.

### Setup Steps

1. **Copy the skill directory** to your Claude Code skills location:
   ```bash
   cp -r prd-brainstorm/ ~/.claude/skills/prd-brainstorm/
   ```

   Or place it wherever your Claude Code instance reads skills from (check your Claude Code configuration).

2. **Verify structure**:
   ```
   prd-brainstorm/
   ├── SKILL.md
   ├── references/
   │   ├── conversation-framework.md
   │   ├── research-playbook.md
   │   └── prd-structure.md
   └── assets/
       └── prd-html-template.html
   ```

3. **Use it**: Start a Claude Code session and describe what you want to build. The skill triggers automatically when Claude detects a product brainstorming or PRD request.

   You can also explicitly invoke it: "Let's brainstorm requirements for a new system I want to build."

---

## What the Agent Produces

### During the Conversation
- Structured questions that build on your answers
- Proactive suggestions based on domain patterns
- Competitor insights when relevant (uses web search)
- Feasibility assessments when complexity is detected
- A consolidation summary for review before PRD generation

### Final Output (your choice of format)
- **Word Document (.docx)**: Professional formatting with tables, callout boxes, cover page, headers/footers, and a sign-off section. Suitable for printing, emailing, and formal sign-off.
- **Interactive HTML**: Sidebar navigation, collapsible sections, scroll tracking, responsive design, visual phase timeline. Suitable for screen-based review and team walkthroughs.
- **Both**: Same content, two formats.

---

## File Inventory

| File | Purpose |
|------|---------|
| `SKILL.md` | Core agent instructions (for Claude Code) |
| `claude-ai-project-prompt.md` | System prompt for Claude.ai Projects |
| `references/conversation-framework.md` | Domain detection signals, question patterns, anti-patterns |
| `references/research-playbook.md` | Competitor analysis, feasibility assessment, build vs buy |
| `references/prd-structure.md` | Dynamic section pool, selection guidance, formatting rules |
| `assets/prd-html-template.html` | Base HTML/CSS/JS template for interactive PRD output |
| `assets/prd-docx-template.js` | Base docx-js template with helpers for Word PRD output |
| `SETUP.md` | This file |
