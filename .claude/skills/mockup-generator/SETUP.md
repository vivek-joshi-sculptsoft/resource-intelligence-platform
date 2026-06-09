# Mockup Generator — Setup Guide

Reads SCREENS.md from module folders and generates interactive HTML mockups or Figma-ready output, with a central `mockups/index.html` review hub.

---

## Setup

### Claude Code
```bash
cp -r mockup-generator/ ~/.claude/skills/
```

### Claude.ai Project
1. Paste `claude-ai-project-prompt.md` as custom instructions
2. Upload knowledge files:
   - `references/themes.md`
   - `references/design-tokens.md`
   - `references/component-library.md`
   - `references/figma-mcp-patterns.md` ← required for Live Figma MCP mode
3. Enable File Creation

---

## Figma MCP Setup (for Live Figma mode)

Live Figma mode uses the **official Figma MCP server** — a remote HTTP server hosted by Figma. No Figma Desktop app, no relay, no plugin required.

### 1. Add the MCP server to Claude Code

```bash
# Recommended: install as a plugin (user-scoped, available in all projects)
claude plugin install figma@claude-plugins-official

# Alternative: add manually
claude mcp add --transport http --scope user figma https://mcp.figma.com/mcp
```

### 2. Authenticate

In Claude Code, run:
```
/mcp
```
Select **figma** → **Authenticate** → complete the OAuth flow in your browser → "Authentication successful."

### 3. Verify connection

```bash
claude "Check Figma connection and list available tools"
```

That's it. No Desktop app, no relay server, no plugin.

> **Note:** The official Figma MCP is free during beta. It will become usage-based paid in future.

---

## Usage

```bash
# Single module (prompts for format A/B/C, then theme)
claude "Generate mockups for module 05-allocation-tracking"

# Specific screen
claude "Mock up the Resource Availability View from module 10"

# All modules
claude "Generate mockups for all modules"

# Explicit format
claude "Generate Live Figma mockups for module 05-allocation-tracking"
claude "Generate HTML mockups for module 05-allocation-tracking"

# Role comparison
claude "Show me Project Detail View as PM vs Engineer"

# Refresh the review index (HTML/export modes)
claude "Regenerate the mockup index"
```

---

## Output

### HTML Mode
```
mockups/
├── index.html                    ← Open this first — module review hub
├── theme-preview-A.html          ← Temporary (pick theme, then discard)
├── theme-preview-B.html
└── theme-preview-C.html

modules/{module}/mockups/
├── screen-name.html              ← Linked from index.html
├── screen-form.html
└── ...
```

### Figma Mode
```
mockups/
├── index.html                    ← Module review hub (links to HTML previews)
└── figma/
    ├── figma-variables.json      ← Import via Figma Variables plugin
    └── import-guide.html         ← Step-by-step import instructions

modules/{module}/mockups/
├── screen-name.html              ← Figma-optimized HTML (use with html.to.design plugin)
└── ...
```

### Live Figma MCP Mode
```
[Figma canvas — no local files generated]

Each module gets its own Figma page.
Screens appear as 1440×900 frames in a 2-column grid.
```

**Start with `mockups/index.html`** — it lists all modules and screens with direct links (HTML/export modes only).

---

## Figma Import Steps

1. Open `mockups/figma/import-guide.html` for full instructions
2. Install the **html.to.design** plugin in Figma
3. Open each `modules/{module}/mockups/*.html` file in Chrome
4. Run the plugin → it converts the page to Figma frames
5. Import `figma-variables.json` via Figma → Resources → Variables → Import

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
| `references/themes.md` | Complete theme definitions (A/B/C) |
| `references/design-tokens.md` | CSS design system and component styles |
| `references/component-library.md` | Reusable HTML/CSS/JS patterns including index page |
| `references/figma-mcp-patterns.md` | MCP tool call patterns, RGB color tables, Figma build order |
