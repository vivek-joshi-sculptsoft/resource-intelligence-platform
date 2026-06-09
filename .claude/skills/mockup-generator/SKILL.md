---
name: mockup-generator
description: "A skill that reads SCREENS.md and SCHEMA.md from a module folder and generates interactive HTML mockups or Figma-ready output with realistic sample data, role-based view toggling, responsive layouts, and interactive elements. First asks HTML or Figma. For HTML: presents 3 theme options, user picks one, all mockups use that theme, and generates a root mockups/index.html for reviewing all modules in one place. Triggers when someone says 'generate mockups', 'create screen mockups', 'mock up this module', 'show me what this looks like', 'create UI previews', or asks to visualize screens from a SCREENS.md file."
---

# Mockup Generator

You read module specification files (SCREENS.md, SCHEMA.md, shared/ACCESS-MATRIX.md) and generate polished mockups that stakeholders can review. You support three output modes: **HTML** (open in browser), **Figma export** (import via plugin), and **Live Figma MCP** (build frames directly in Figma via the official Figma MCP server).

## Core Principles

**Format first, theme second, mockups third.** Ask for output format before anything else.

**Mockups are for stakeholder alignment, not engineering.** They exist so non-technical people can see and react to the UI before production code is written.

**Use realistic data, never lorem ipsum.** Show "Vivek Sharma — Tech Lead — 60% allocated to Project Phoenix." Not "User 1 — Role A — XX%."

**Show role-based views.** Every mockup includes a role switcher so reviewers can see exactly what's hidden/shown for each role.

**Interactive but throwaway.** Tabs switch, forms have inputs, filters exist — but they don't actually filter.

---

## Workflow

### Phase 0a: Format Selection (always runs first)

Ask the user:

> "Which output format?
> A) **HTML** — self-contained files, open directly in browser
> B) **Figma (file export)** — Figma-import-ready HTML + design tokens JSON
> C) **Live Figma (MCP)** — build frames directly inside your open Figma file in real time"

- **HTML** → proceed with Phase 0 (theme selection), then Phases 1–4
- **Figma file export** → skip theme selection, proceed with Phases 1–3 using Figma export mode, then Phase 4
- **Live Figma (MCP)** → check MCP availability first, then proceed with Phases 0 (theme), 1–4 using MCP mode

**Subsequent runs (format already chosen in conversation):** Skip this question, use the same format.

#### Live Figma MCP — Availability Check

Before proceeding with Live Figma mode, list available Figma MCP tools and look for write/create capability. If no Figma MCP tools are found or only read tools are available:

```
"Figma MCP not connected (or read-only). To use Live Figma mode:
 1. claude mcp add --transport http --scope user figma https://mcp.figma.com/mcp
 2. Run /mcp → figma → Authenticate (OAuth)

 Falling back to Figma file export mode instead."
```

If write tools are found, get current document info and confirm: "Connected to Figma — [file name]. Which page should I build on? (I'll create one frame per screen.)"

---

### Phase 0: Theme Selection (HTML path only)

Before any module mockups, generate 3 theme preview files. Each shows the same 3 sample screens in a different visual style so the user compares aesthetics, not content.

**Preview Screen 1: Login Page**
- App name, logo placeholder, email/password inputs, login button, "Forgot password?" link

**Preview Screen 2: Dashboard Overview**
- 4 KPI cards (utilization %, bench count, active projects, revenue)
- A mini data table (5 rows of resource assignments)
- Sidebar navigation sketch

**Preview Screen 3: Data Entry Form**
- Representative form (e.g., "Add Assignment")
- Inputs, dropdowns, date pickers, checkboxes
- Validation error state on one field
- Cancel/Save buttons

**Output:**
```
mockups/
├── theme-preview-A.html    ← Clean Minimal
├── theme-preview-B.html    ← Professional Corporate
└── theme-preview-C.html    ← Modern Vibrant
```

Present all 3 and ask: "Which theme should I use for all mockups?"

Read `references/themes.md` for complete theme definitions.

**After selection:** Store the chosen theme's CSS variables. Use them for all subsequent mockup generation and for `mockups/index.html`.

---

### Phase 1: Read Module Specs

Read the module files:

```
modules/{module-name}/
├── SCREENS.md          ← Primary input: view specifications
├── SCHEMA.md           ← Entity fields for realistic data generation
└── REQUIREMENTS.md     ← Feature context

shared/
├── ACCESS-MATRIX.md    ← Role-based field visibility
└── ENTITIES.md         ← Full entity definitions
```

---

### Phase 2: Generate Sample Data

Create a realistic, consistent dataset. The same people, projects, and clients appear across all screens.

**Data rules:**
- Indian names: Vivek Sharma, Priya Patel, Arjun Mehta, Neha Gupta, Rajesh Kumar, Sneha Reddy, Amit Joshi, Kavita Nair, Rohan Das, Anita Singh
- Realistic companies: Nexus Healthcare, Pinnacle Finance, Meridian Logistics, Atlas Retail, Vertex Consulting
- Project names: Project Phoenix, Atlas Migration, Meridian API, Nexus Patient Portal, Vertex Analytics
- Dates in Jul–Dec 2026 range
- Varied percentages: 20%, 40%, 50%, 60%, 80%, 100% — not uniform
- At least one shadow resource, one over-allocated (>100%), one bench resource
- At least one multi-currency entry (USD with exchange rate)
- Mix of statuses (mostly ACTIVE, some COMPLETED, ON_HOLD)

---

### Phase 3: Build Mockups

#### HTML Mode

For each screen in SCREENS.md, generate one HTML file:

```
modules/{module-name}/mockups/
├── {screen-name}.html
├── {screen-name-form}.html
└── ...
```

Each file includes:

1. **Role Switcher Bar** — fixed at top, buttons for each role, active role highlighted, restricted fields show 🔒
2. **Page Header** — title, breadcrumb, primary action button
3. **Content** — matching SCREENS.md exactly: tables, forms, cards, widgets, tabs
4. **Empty State Toggle** — button to preview zero-data state
5. **Self-contained** — inline CSS + JS, no external dependencies, opens in any browser

Apply the selected theme's CSS variables from `references/design-tokens.md`.
Read `references/component-library.md` for reusable HTML/CSS/JS patterns.

#### Figma File Export Mode

Generate the same screens as HTML but optimized for the "HTML to Figma" / "html.to.design" browser plugin:

- Use semantic, flat HTML structure (avoid deeply nested CSS grid/flexbox — Figma import works better with simpler layouts)
- Prefer explicit `width`/`height` on containers where possible
- Use `position: absolute` sparingly — plugin handles static flow better
- No CSS animations or transitions (Figma ignores them)
- All text must be in actual `<p>`, `<span>`, `<h1>`–`<h6>` tags — no CSS `content:`
- Use neutral theme (clean white/gray/blue palette — designer will apply Figma styles after import)

Also generate:
```
mockups/figma/
├── figma-variables.json    ← Design tokens as Figma Variables (importable via Figma Variables plugin)
└── import-guide.html       ← Step-by-step instructions for importing into Figma
```

**figma-variables.json format:**
```json
{
  "name": "{Project Name} Design Tokens",
  "collections": [
    {
      "name": "Colors",
      "modes": [{ "name": "Light" }],
      "variables": [
        { "name": "primary", "type": "COLOR", "values": { "Light": "#1B3A5C" } },
        { "name": "accent", "type": "COLOR", "values": { "Light": "#0d9488" } },
        { "name": "background/page", "type": "COLOR", "values": { "Light": "#f8fafc" } },
        { "name": "background/card", "type": "COLOR", "values": { "Light": "#ffffff" } },
        { "name": "text/primary", "type": "COLOR", "values": { "Light": "#334155" } },
        { "name": "text/secondary", "type": "COLOR", "values": { "Light": "#64748b" } },
        { "name": "border/default", "type": "COLOR", "values": { "Light": "#e2e8f0" } },
        { "name": "status/active", "type": "COLOR", "values": { "Light": "#22c55e" } },
        { "name": "status/warning", "type": "COLOR", "values": { "Light": "#f59e0b" } },
        { "name": "status/danger", "type": "COLOR", "values": { "Light": "#ef4444" } }
      ]
    },
    {
      "name": "Spacing",
      "modes": [{ "name": "Default" }],
      "variables": [
        { "name": "sp-1", "type": "FLOAT", "values": { "Default": 4 } },
        { "name": "sp-2", "type": "FLOAT", "values": { "Default": 8 } },
        { "name": "sp-4", "type": "FLOAT", "values": { "Default": 16 } },
        { "name": "sp-6", "type": "FLOAT", "values": { "Default": 24 } },
        { "name": "sp-8", "type": "FLOAT", "values": { "Default": 32 } }
      ]
    },
    {
      "name": "Typography",
      "modes": [{ "name": "Default" }],
      "variables": [
        { "name": "size/xs", "type": "FLOAT", "values": { "Default": 11 } },
        { "name": "size/sm", "type": "FLOAT", "values": { "Default": 12 } },
        { "name": "size/base", "type": "FLOAT", "values": { "Default": 14 } },
        { "name": "size/lg", "type": "FLOAT", "values": { "Default": 18 } },
        { "name": "size/xl", "type": "FLOAT", "values": { "Default": 24 } }
      ]
    }
  ]
}
```

#### Live Figma (MCP) Mode

Read `references/figma-mcp-patterns.md` before building any screen. Build each screen as a 1440×900 Figma frame using MCP tool calls.

**Per module workflow:**
1. Confirm the user has switched to the correct Figma page
2. For each screen in SCREENS.md (in order):
   - Calculate canvas position using the 2-column grid layout (see figma-mcp-patterns.md → Grid Layout)
   - Build the screen frame with: role bar, sidebar, page header, then screen-specific content
   - Use realistic sample data from Phase 2
   - Report each screen as it completes: "✓ Built 'Allocation List' (frame ID: xxx)"
3. After all screens: build the `_Overview` summary frame
4. Report total: "Built N screens on page '{Page Name}'. Switch to that page in Figma to review."

**Screen type → content pattern mapping:**
| SCREENS.md screen type | Pattern to use |
|------------------------|----------------|
| List / Table view | KPI Cards Row + Data Table |
| Form / Add / Edit | Form Screen |
| Dashboard / Overview | KPI Cards Row + Data Table (mini) + Charts placeholder |
| Detail / Profile | Two-column layout: left info card, right tabs with table |
| Calendar / Schedule | Calendar grid (rectangles for day cells, text for events) |
| Settings | Form Screen (grouped sections) |

**MCP tool call budget per screen:** ~15–25 calls. Prioritize structure and data over pixel perfection. A recognizable screen with realistic data is better than a pixel-perfect screen with placeholder text.

**Theme application:** Use RGB values from `references/figma-mcp-patterns.md` → Theme Colors for the selected theme. Apply consistently — role bar bg, sidebar bg, accent buttons, table headers all come from the theme table.

**Tool names:** The official Figma MCP does not publish a fixed tool list. Discover available tools at runtime (see `references/figma-mcp-patterns.md` → MCP Availability Check). Map each needed operation to the best-matching discovered tool.

---

### Phase 4: Present + Generate Index

#### Live Figma (MCP) Mode — Skip index.html
In MCP mode, the Figma canvas IS the review surface. Instead of index.html, report a summary:
```
✓ Built 4 screens for "Allocation Tracking" on page 'Module 05'
  — Allocation List (frame: 1234)
  — Add Assignment (frame: 1235)
  — Resource Calendar (frame: 1236)
  — Over-Allocation Alerts (frame: 1237)

Switch to the 'Module 05' page in Figma to review. All frames are on a 2-column grid.
```

#### HTML / Figma Export Mode — Generate mockups/index.html

After generating mockups for each module, create or update `mockups/index.html`. This file is the central hub for reviewing all mockups.

**Index page structure:**
- **Top bar:** Project name, output mode badge (HTML/Figma), total screen count, theme badge (HTML mode)
- **Left sidebar:** Module list — each entry shows module number, name, screen count, and completion checkmark. Clicking switches the main panel.
- **Main panel:** For the selected module, show a responsive grid of screen cards. Each card has:
  - Screen name (bold)
  - Screen type icon (📋 list, 📝 form, 📊 dashboard, 🗓 calendar, ⚙️ settings)
  - One-line description from SCREENS.md
  - "Open →" link button (opens the HTML file in a new tab)
- **Module actions bar:** "Open All Screens" button (opens all screens for the module in new tabs)
- **No external deps** — self-contained, inline CSS + JS

**Data embedding:** Embed all module/screen metadata as a JS object at the top of the script:

```javascript
const MOCKUP_DATA = {
  project: "Resource Management System",
  theme: "Professional Corporate",
  mode: "html",
  modules: [
    {
      id: "05-allocation-tracking",
      name: "Allocation Tracking",
      screens: [
        {
          name: "Allocation List",
          type: "list",
          description: "Table of all resource allocations with filters",
          file: "../modules/05-allocation-tracking/mockups/allocation-list.html"
        },
        {
          name: "Add Assignment",
          type: "form",
          description: "Form to create a new resource-project assignment",
          file: "../modules/05-allocation-tracking/mockups/add-assignment.html"
        }
      ]
    }
  ]
};
```

Read `references/component-library.md` → **Index Page** section for the full HTML/CSS/JS pattern.

#### Present

List all generated mockups:
```
✓ mockups/index.html — Module review hub (3 modules, 12 screens)

Module 05 — Allocation Tracking (4 screens):
  • modules/05-allocation-tracking/mockups/allocation-list.html
  • modules/05-allocation-tracking/mockups/add-assignment.html
  • modules/05-allocation-tracking/mockups/resource-calendar.html
  • modules/05-allocation-tracking/mockups/over-allocation-alerts.html
```

---

## Theme System

Read `references/themes.md` for full theme definitions. Summary:

### Theme A: Clean Minimal
- White background, light gray cards, thin borders, teal accent
- Best for: readability-first tools

### Theme B: Professional Corporate
- Navy sidebar/headers, white content, blue accents, dense tables
- Best for: data-heavy dashboards, enterprise tools

### Theme C: Modern Vibrant
- Purple/indigo gradients, rounded cards, colorful accents, elevated shadows
- Best for: modern, approachable tools

All themes share: same typography scale, 8px spacing grid, same component structure, same role switcher behavior, same responsive breakpoints.

---

## Processing Modes

**First run (HTML):**
```
"Generate mockups for module 05-allocation-tracking"
→ "A) HTML  B) Figma export  C) Live Figma (MCP)?"
→ User picks A → "Here are 3 theme options..."
→ User picks theme
→ Generates module mockups + creates mockups/index.html
```

**First run (Live Figma MCP):**
```
"Generate mockups for module 05-allocation-tracking"
→ User picks C
→ Lists Figma MCP tools — write tools found ✓
→ "Connected to 'Resource Manager'. Which page? (or I'll use current)"
→ "Here are 3 theme options..." (shows theme previews as HTML files)
→ User picks theme
→ Builds frames in Figma via MCP tools, reports frame IDs
```

**Subsequent module (format + theme set):**
```
"Now generate mockups for module 03-project-management"
→ Uses existing format + theme, skips both questions
→ HTML: generates mockups + updates index.html
→ MCP: builds frames on new/same Figma page
```

**Theme reset:**
```
"Show me the theme options again"
→ Regenerates 3 HTML preview files
```

**Index-only refresh (HTML/export modes):**
```
"Regenerate the mockup index"
→ Rebuilds mockups/index.html from current module/screen inventory
```

---

## Reference Files

| File | When to Read |
|------|-------------|
| `references/themes.md` | Phase 0 — generating theme previews |
| `references/design-tokens.md` | Phase 3 (HTML/export) — applying selected theme's CSS |
| `references/component-library.md` | Phase 3 + Phase 4 (HTML/export) — reusable HTML/CSS/JS patterns including index page |
| `references/figma-mcp-patterns.md` | Phase 3 (Live Figma MCP) — MCP tool call patterns, RGB color tables, screen build order |
