# Figma MCP Patterns

Reusable patterns for building mockup screens directly in Figma via the **official Figma MCP server** (`https://mcp.figma.com/mcp`).

The official Figma MCP does not publish a fixed tool list — tools may vary by beta version. Always **discover available tools at runtime** before building.

---

## MCP Availability Check + Tool Discovery

Before building anything, discover what Figma MCP tools are available:

```
1. List all tools from the figma MCP server (use ToolSearch or list_tools)
2. Look for tools with write/create capability — keywords: "create", "write", "canvas", "frame", "node"
3. If no write tools found → fall back to Figma file-export mode, notify user:
   "Figma MCP is connected but no write tools detected (read-only mode).
    Try re-authenticating or check that your Figma plan supports canvas writes."
4. If no figma MCP at all → fall back to Figma file-export mode:
   "Figma MCP not found. Add it with:
    claude mcp add --transport http --scope user figma https://mcp.figma.com/mcp
    Then run /mcp → figma → Authenticate."
```

**Map discovered tools to operations:**

| Operation needed | Look for tool with these keywords |
|-----------------|-----------------------------------|
| Get file/document info | `get`, `file`, `document`, `info` |
| Create a frame/container | `create`, `frame`, `node`, `write`, `canvas` |
| Create text | `create`, `text`, `write` |
| Create rectangle/shape | `create`, `rectangle`, `shape`, `node` |
| Set color/fill | `fill`, `color`, `style`, `set` |
| Set layout (auto layout) | `layout`, `padding`, `spacing`, `align` |
| Set corner radius | `corner`, `radius`, `style` |
| Move/position node | `move`, `position`, `x`, `y` |
| Resize node | `resize`, `size`, `width`, `height` |
| Clone/duplicate node | `clone`, `duplicate`, `copy` |

Use the best-matching tool for each operation. If a single tool covers multiple operations (e.g. a general `write_to_canvas` or `create_node` with a type parameter), use it accordingly.

---

## Document & Page Setup

### Get current file info
```
get_document_info
→ Returns: file name, current page, canvas bounds
```

### Create a page per module
One Figma page per module keeps screens organized.
```
# Pages cannot be created via most MCP tools — ask user to create the page manually
# and switch to it before generating:

Say: "Please create a Figma page named '{Module Name}' and switch to it. 
      I'll build all screens for this module on that page."

# After user confirms, proceed
get_document_info   ← verify we're on the right page
```

---

## Screen Frame (Top-Level)

Every screen is a 1440×900 frame. Name format: `{ScreenName}` (no prefix).

```
create_frame
  name: "Allocation List"
  x: {column_offset}     ← see Grid Layout section
  y: 0
  width: 1440
  height: 900

→ store returned frameId as SCREEN_FRAME_ID
```

Apply page background:
```
set_fill_color
  nodeId: SCREEN_FRAME_ID
  r: {bg_r}  g: {bg_g}  b: {bg_b}   ← from selected theme (see Theme Colors)
```

---

## Grid Layout

Place screens in a grid so they're easy to scan on the canvas. 2 columns, 80px gap.

```
Column 0: x = 0
Column 1: x = 1520     (1440 + 80)

Row spacing: y += 980  (900 + 80)

Formula:
  col = screenIndex % 2
  row = Math.floor(screenIndex / 2)
  x = col * 1520
  y = row * 980
```

---

## Role Switcher Bar

Fixed at top of every screen. Dark background strip, role buttons.

```
# Bar container
create_frame
  name: "RoleBar"
  parentId: SCREEN_FRAME_ID
  x: 0  y: 0  width: 1440  height: 48
set_fill_color nodeId: ROLEBAR_ID  ← role_bar_bg color from theme
set_layout_mode nodeId: ROLEBAR_ID  mode: HORIZONTAL
set_padding nodeId: ROLEBAR_ID  top:0 right:24 bottom:0 left:24
set_item_spacing nodeId: ROLEBAR_ID  spacing: 8
set_axis_align nodeId: ROLEBAR_ID  primaryAxis: MIN  counterAxis: CENTER

# "Viewing as:" label
create_text
  parentId: ROLEBAR_ID
  text: "VIEWING AS:"
  fontSize: 11  fontWeight: 700
  color: {muted text color from theme}

# Role buttons — repeat for each role: CEO, CTO, DM, PM, Finance, HR, Engineer
# Active role gets accent color background

create_frame  name: "Btn-CEO"  parentId: ROLEBAR_ID  width: 64  height: 28
set_fill_color ← accent color (active) or transparent (inactive)
set_corner_radius ← 9999 (pill shape)

create_text  parentId: Btn-CEO_ID  text: "CEO"
  fontSize: 12  fontWeight: 600  color: white (active) or muted (inactive)
```

---

## Sidebar Navigation

Left sidebar, 220px wide, full height minus role bar.

```
create_frame
  name: "Sidebar"
  parentId: SCREEN_FRAME_ID
  x: 0  y: 48  width: 220  height: 852
set_fill_color ← sidebar_bg from theme
set_layout_mode mode: VERTICAL
set_padding top:16 right:0 bottom:16 left:0
set_item_spacing spacing: 2

# App logo / name area
create_frame  name: "AppLogo"  parentId: SIDEBAR_ID  width: 220  height: 56
set_padding left:20
create_text  text: "{App Name}"  fontSize: 16  fontWeight: 700  color: header_text

# Nav items — repeat for each module
create_frame  name: "NavItem-Allocation"  parentId: SIDEBAR_ID
  width: 220  height: 40
set_layout_mode mode: HORIZONTAL
set_padding left:20 right:16
set_item_spacing spacing: 10
# Active item: accent background
set_fill_color ← sidebar_active_bg (active) or transparent (inactive)
create_text  text: "Allocation Tracking"
  fontSize: 14  color: sidebar_active_text (active) or sidebar_text (inactive)
```

---

## Page Header

Title area at top of main content area.

```
# Content area starts at x:220, y:48
create_frame
  name: "PageHeader"
  parentId: SCREEN_FRAME_ID
  x: 220  y: 48  width: 1220  height: 72
set_fill_color ← bg_card or bg_header from theme
set_layout_mode mode: HORIZONTAL
set_padding left:32 right:32
set_axis_align primaryAxis: SPACE_BETWEEN  counterAxis: CENTER

# Left: breadcrumb + title stack
create_frame  name: "TitleStack"  parentId: PAGEHEADER_ID
set_layout_mode mode: VERTICAL  set_item_spacing spacing: 4
create_text  text: "Home / Allocation Tracking"
  fontSize: 12  color: text_muted
create_text  text: "Allocation Tracking"
  fontSize: 20  fontWeight: 700  color: primary

# Right: primary action button
create_frame  name: "BtnAddAssignment"  parentId: PAGEHEADER_ID
  width: 160  height: 38
set_fill_color ← btn_primary_bg
set_corner_radius ← radius_btn
create_text  text: "+ Add Assignment"
  fontSize: 14  fontWeight: 600  color: white
```

---

## KPI Cards Row

```
# KPI container
create_frame
  name: "KPIRow"
  parentId: SCREEN_FRAME_ID
  x: 236  y: 136  width: 1188  height: 104
set_layout_mode mode: HORIZONTAL
set_item_spacing spacing: 16

# Repeat for each KPI (4 total)
create_frame  name: "KPI-Utilization"  parentId: KPIROW_ID
  width: 282  height: 104
set_fill_color ← bg_card
set_corner_radius ← radius_card
set_layout_mode mode: VERTICAL
set_padding top:20 right:20 bottom:20 left:20
set_item_spacing spacing: 4

create_text  text: "Billable Utilization"
  fontSize: 12  fontWeight: 500  color: kpi_label_color
create_text  text: "74%"
  fontSize: 28  fontWeight: 700  color: kpi_value_color
create_text  text: "↑ 3% from last month"
  fontSize: 12  color: success_color
```

---

## Data Table

```
# Table card
create_frame
  name: "TableCard"
  parentId: SCREEN_FRAME_ID
  x: 236  y: 256  width: 1188  height: 480
set_fill_color ← bg_card
set_corner_radius ← radius_card
set_layout_mode mode: VERTICAL

# Table header row
create_frame  name: "TableHeader"  parentId: TABLECARD_ID
  width: 1188  height: 40
set_fill_color ← table_header_bg
set_layout_mode mode: HORIZONTAL
set_padding left:16 right:16
set_axis_align counterAxis: CENTER

# Column headers — repeat for each column
create_text  text: "RESOURCE"
  fontSize: 11  fontWeight: 700  color: table_header_text
  (set width proportionally, e.g. 200px for name columns, 100px for %)

# Data rows — repeat for each row (use clone_node after first row)
create_frame  name: "Row-1"  parentId: TABLECARD_ID
  width: 1188  height: 48
set_fill_color ← bg_card (odd) or bg_stripe (even)
set_layout_mode mode: HORIZONTAL
set_padding left:16 right:16
set_axis_align counterAxis: CENTER
set_item_spacing spacing: 0

create_text  text: "Vivek Sharma"  fontSize: 13  fontWeight: 600  color: text_primary
create_text  text: "Tech Lead"  fontSize: 13  color: text_secondary
create_text  text: "60%"  fontSize: 13  color: text_primary
# ... other columns

# Clone rows for efficiency
clone_node  nodeId: ROW1_ID  → ROW2_ID
set_multiple_text_contents  nodeId: ROW2_ID  contents: [...]
move_node  nodeId: ROW2_ID  x: 0  y: 48   ← relative within parent
```

---

## Status Badge

```
create_frame  name: "Badge-Active"
  width: 64  height: 22
set_fill_color  r:0.82 g:0.98 b:0.9   ← #d1fae5
set_corner_radius  9999

create_text  text: "ACTIVE"
  fontSize: 11  fontWeight: 700
  color: r:0.02 g:0.37 b:0.27   ← #065f46
# center text inside badge frame
```

Badge colors by status:
- ACTIVE: bg `#d1fae5` text `#065f46`
- COMPLETED: bg `#dbeafe` text `#1e40af`
- ON_HOLD: bg `#fef3c7` text `#92400e`
- OVER_ALLOCATED: bg `#fee2e2` text `#991b1b`
- SHADOW: bg `#f3e8ff` text `#6b21a8`

---

## Form Screen

```
# Form card
create_frame  name: "FormCard"
  parentId: SCREEN_FRAME_ID
  x: 236  y: 136  width: 680  height: 600
set_fill_color ← bg_card
set_corner_radius ← radius_card
set_layout_mode mode: VERTICAL
set_padding top:24 right:24 bottom:24 left:24
set_item_spacing spacing: 16

# Card header
create_frame  name: "CardHeader"  ...  width: 632  height: 48
create_text  text: "Add Assignment"  fontSize: 16  fontWeight: 600  color: primary

# Field group — repeat for each field
create_frame  name: "Field-Resource"  parentId: FORMCARD_ID
  width: 632
set_layout_mode mode: VERTICAL  set_item_spacing spacing: 6

create_text  text: "Resource *"
  fontSize: 12  fontWeight: 600  color: text_secondary

create_frame  name: "Input-Resource"  width: 632  height: 38
set_fill_color ← bg_input
set_corner_radius ← radius_input
set_stroke_color ← border_color
# stroke width: 1
create_text  text: "Select resource..."
  fontSize: 14  color: text_muted  x: 12  y: 10

# Inline two-column fields
create_frame  name: "FieldRow"  parentId: FORMCARD_ID  width: 632
set_layout_mode mode: HORIZONTAL  set_item_spacing spacing: 16
# Add two field groups, each width: 308

# Error field
set_stroke_color  nodeId: ERROR_INPUT_ID  ← danger color
create_text  text: "Billability cannot exceed allocation percentage"
  fontSize: 12  color: danger_color

# Action buttons
create_frame  name: "FormActions"  parentId: FORMCARD_ID
  width: 632  height: 38
set_layout_mode mode: HORIZONTAL
set_axis_align primaryAxis: END  set_item_spacing spacing: 12

create_frame  name: "BtnCancel"  width: 80  height: 38
set_fill_color ← bg_hover  set_corner_radius ← radius_btn
create_text  text: "Cancel"  fontSize: 14  fontWeight: 500

create_frame  name: "BtnSave"  width: 140  height: 38
set_fill_color ← btn_primary_bg  set_corner_radius ← radius_btn
create_text  text: "Save Assignment"  fontSize: 14  fontWeight: 600  color: white
```

---

## Theme Colors (RGB values for set_fill_color)

`set_fill_color` takes r/g/b as 0–1 floats. Convert hex:  `r = hex_r / 255`.

### Theme A: Clean Minimal
| Token | Hex | r | g | b |
|-------|-----|---|---|---|
| bg_page | #fafafa | 0.98 | 0.98 | 0.98 |
| bg_card | #ffffff | 1 | 1 | 1 |
| sidebar_bg | #ffffff | 1 | 1 | 1 |
| role_bar_bg | #0f172a | 0.059 | 0.09 | 0.165 |
| primary | #0f172a | 0.059 | 0.09 | 0.165 |
| accent | #0d9488 | 0.051 | 0.58 | 0.533 |
| text_primary | #1e293b | 0.118 | 0.161 | 0.231 |
| text_secondary | #64748b | 0.392 | 0.455 | 0.545 |
| text_muted | #a1a1aa | 0.631 | 0.631 | 0.667 |
| border | #e5e5e5 | 0.898 | 0.898 | 0.898 |
| table_header_bg | #fafafa | 0.98 | 0.98 | 0.98 |
| table_header_text | #64748b | 0.392 | 0.455 | 0.545 |
| btn_primary | #0d9488 | 0.051 | 0.58 | 0.533 |

### Theme B: Professional Corporate
| Token | Hex | r | g | b |
|-------|-----|---|---|---|
| bg_page | #f1f5f9 | 0.945 | 0.961 | 0.976 |
| bg_card | #ffffff | 1 | 1 | 1 |
| sidebar_bg | #0f2b45 | 0.059 | 0.169 | 0.271 |
| role_bar_bg | #0a1f33 | 0.039 | 0.122 | 0.2 |
| primary | #1B3A5C | 0.106 | 0.227 | 0.361 |
| accent | #2c7be5 | 0.173 | 0.482 | 0.898 |
| text_primary | #334155 | 0.2 | 0.255 | 0.333 |
| text_secondary | #64748b | 0.392 | 0.455 | 0.545 |
| sidebar_text | #8da4bc | 0.553 | 0.643 | 0.737 |
| sidebar_active_bg | #2c7be526 | 0.173 | 0.482 | 0.898 (opacity 0.15) |
| table_header_bg | #1B3A5C | 0.106 | 0.227 | 0.361 |
| table_header_text | #ffffff | 1 | 1 | 1 |
| btn_primary | #2c7be5 | 0.173 | 0.482 | 0.898 |

### Theme C: Modern Vibrant
| Token | Hex | r | g | b |
|-------|-----|---|---|---|
| bg_page | #f5f3ff | 0.961 | 0.953 | 1 |
| bg_card | #ffffff | 1 | 1 | 1 |
| sidebar_bg | #faf5ff | 0.98 | 0.961 | 1 |
| role_bar_bg | #1e1b4b | 0.118 | 0.106 | 0.294 |
| primary | #6d28d9 | 0.427 | 0.157 | 0.851 |
| accent | #0d9488 | 0.051 | 0.58 | 0.533 |
| text_primary | #1e1b4b | 0.118 | 0.106 | 0.294 |
| text_secondary | #6b7280 | 0.42 | 0.447 | 0.502 |
| table_header_bg | #6d28d9 | 0.427 | 0.157 | 0.851 |
| table_header_text | #ffffff | 1 | 1 | 1 |
| btn_primary | #6d28d9 | 0.427 | 0.157 | 0.851 |

---

## Screen Overview Frame

After all screens are built, create one summary "storyboard" frame.

```
create_frame
  name: "_Overview — {Module Name}"
  x: 0  y: {last_row_y + 1060}
  width: {total_canvas_width}  height: 400

create_text  text: "{Module Name} — {N} Screens"
  fontSize: 24  fontWeight: 700

# Add miniature labels for each screen
# (just text labels — thumbnails require export_node_as_image)
create_text  text: "1. Allocation List  |  2. Add Assignment  |  ..."
  fontSize: 14  color: text_secondary
```

---

## Build Order per Screen

1. `get_document_info` — verify on correct page
2. `create_frame` — top-level screen frame, set bg
3. `create_frame` + `set_fill_color` — role bar, sidebar, page header
4. Content area frames (KPIs, table, form — depending on screen type)
5. `create_text` nodes for all data (realistic sample data)
6. `set_fill_color` / `set_corner_radius` on each container
7. `set_layout_mode` + `set_padding` + `set_item_spacing` for auto-layout sections
8. Status badges with correct colors
9. Report the frame ID and position back to user

**Aim for ~15–25 MCP calls per screen.** Don't build pixel-perfect — build scannable and recognizable.
