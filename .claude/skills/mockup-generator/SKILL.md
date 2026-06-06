---
name: mockup-generator
description: "A skill that reads SCREENS.md and SCHEMA.md from a module folder and generates interactive HTML mockups with realistic sample data, role-based view toggling, responsive layouts, and interactive elements. Starts by presenting 3 theme options with preview screens — user picks one, then all mockups use that theme. Triggers when someone says 'generate mockups', 'create screen mockups', 'mock up this module', 'show me what this looks like', 'create UI previews', or asks to visualize screens from a SCREENS.md file."
---

# Mockup Generator

You read module specification files (SCREENS.md, SCHEMA.md, shared/ACCESS-MATRIX.md) and generate polished, interactive HTML mockups that stakeholders can review in a browser. Before generating any module mockups, you present 3 theme options and let the user choose the visual direction.

## Core Principles

**Theme first, mockups second.** Don't generate module mockups until the user has picked a theme. The theme sets the visual identity for everything that follows.

**Mockups are for stakeholder alignment, not engineering.** They exist so non-technical people can see and react to the UI before production code is written.

**Use realistic data, never lorem ipsum.** Show "Vivek Sharma — Tech Lead — 60% allocated to Project Phoenix." Not "User 1 — Role A — XX%."

**Show role-based views.** Every mockup includes a role switcher so reviewers can see exactly what's hidden/shown for each role.

**Interactive but throwaway.** Tabs switch, forms have inputs, filters exist — but they don't actually filter. Spatial understanding, not functionality.

---

## Workflow

### Phase 0: Theme Selection (always runs first)

Before any module mockups, generate 3 theme preview files. Each preview contains the same 3 sample screens rendered in a different visual theme so the user can compare apples to apples:

**Preview Screen 1: Login Page**
- App name, logo placeholder, email/password inputs, login button, "Forgot password?" link
- Uses the project name from PRD if available

**Preview Screen 2: Dashboard Overview**
- 4 KPI cards (utilization %, bench count, active projects, revenue)
- A mini data table (5 rows of resource assignments)
- Sidebar navigation sketch

**Preview Screen 3: Data Entry Form**
- A representative form (e.g., "Add Assignment" or relevant to the project)
- Inputs, dropdowns, date pickers, checkboxes
- Validation error state on one field
- Cancel/Save buttons

All 3 themes show identical data and layout — only the visual styling changes. This ensures the user is choosing aesthetics, not content.

**Output:**
```
mockups/
├── theme-preview-A.html    ← Clean Minimal
├── theme-preview-B.html    ← Professional Corporate  
└── theme-preview-C.html    ← Modern Vibrant
```

Present all 3 and ask: "Which theme should I use for all mockups?"

Read `references/themes.md` for the complete definition of each theme.

**After selection:** Store the chosen theme's design tokens and use them for all subsequent mockup generation. Delete or ignore the preview files.

### Phase 1: Read Module Specs

Once a theme is selected, read the module files:

```
modules/{module-name}/
├── SCREENS.md          ← Primary input: view specifications
├── SCHEMA.md           ← Entity fields for realistic data generation
└── REQUIREMENTS.md     ← Feature context

shared/
├── ACCESS-MATRIX.md    ← Role-based field visibility
└── ENTITIES.md         ← Full entity definitions
```

### Phase 2: Generate Sample Data

Create a realistic, consistent dataset for this module. The same people, projects, and clients should appear across all screens.

**Data rules:**
- Indian names: Vivek Sharma, Priya Patel, Arjun Mehta, Neha Gupta, Rajesh Kumar, Sneha Reddy, Amit Joshi, Kavita Nair, Rohan Das, Anita Singh
- Realistic companies: Nexus Healthcare, Pinnacle Finance, Meridian Logistics, Atlas Retail, Vertex Consulting
- Project names: Project Phoenix, Atlas Migration, Meridian API, Nexus Patient Portal, Vertex Analytics
- Dates in Jul-Dec 2026 range
- Varied percentages: 20%, 40%, 50%, 60%, 80%, 100% — not uniform
- At least one shadow resource, one over-allocated (>100%), one bench resource
- At least one multi-currency entry (USD with exchange rate)
- Mix of statuses (mostly ACTIVE, some COMPLETED, ON_HOLD)

### Phase 3: Build Mockups

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

### Phase 4: Present

List all generated mockups with file paths and a one-line description of each screen.

---

## Theme System

Read `references/themes.md` for full theme definitions. Summary:

### Theme A: Clean Minimal
- White background, very light gray cards, thin borders
- Single accent color (teal/blue), minimal use of dark backgrounds
- Lots of whitespace, airy feel
- Best for: tools that prioritize readability and simplicity

### Theme B: Professional Corporate
- Navy sidebar/headers, white content area, structured layout
- Navy + teal color scheme, data-dense tables
- Darker visual anchors, more visual hierarchy
- Best for: data-heavy dashboards, enterprise tools

### Theme C: Modern Vibrant
- Subtle gradients, rounded cards with shadows, colorful accents
- Purple/indigo primary, gradient backgrounds, playful badges
- More visual personality, friendly feel
- Best for: tools that want to feel modern and approachable

All themes share:
- Same typography scale (system fonts)
- Same spacing grid (8px)
- Same component structure (tables, forms, cards, badges)
- Same role switcher behavior
- Same responsive breakpoints

---

## Processing Modes

**First run (no theme selected):**
```
"Generate mockups for module 05-allocation-tracking"
→ "I'll first show you 3 theme options. Here are previews..."
→ User picks one
→ Generates module mockups in that theme
```

**Subsequent runs (theme already selected in conversation):**
```
"Now generate mockups for module 03-project-management"
→ Uses the previously selected theme, skips preview
```

**Theme reset:**
```
"Show me the theme options again"
→ Regenerates 3 previews
```

**Single screen:**
```
"Mock up the Resource Availability View"
→ If no theme selected, show previews first
→ Then generate that one screen
```

---

## Reference Files

| File | When to Read |
|------|-------------|
| `references/themes.md` | Phase 0 — generating theme previews |
| `references/design-tokens.md` | Phase 3 — applying selected theme's CSS |
| `references/component-library.md` | Phase 3 — reusable HTML/CSS/JS patterns |
