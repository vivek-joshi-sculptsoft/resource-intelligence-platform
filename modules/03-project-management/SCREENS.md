# Module 03: Project Management — Screen Specifications

## Screen: Project List
**Route:** `/projects`
**Audience:** CEO, CTO, DM, PM, Finance, HR (Engineer has no access)
**Layout:** Full-width table with filter bar and action header.

### Components
- Filter bar: status dropdown, type dropdown, client dropdown, DM dropdown
- Search input: by project name
- "Add Project" button (CEO, CTO, DM only)
- Project table with column sort

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Name | Project.name | Link to detail |
| Client | Client.name | |
| Type | Project.type | Badge (FP / T&M / Onboarding) |
| Status | Project.status | Colored badge |
| DM | Resource.name (dm_id) | |
| PM | Resource.name (pm_id) | |
| Start Date | Project.start_date | |
| Contract End | Project.contract_end_date | Highlighted if expiring soon |

### Actions
- Click row → Project detail
- Add Project → `/projects/new`

### Empty State
"No projects found. Try adjusting your filters or create a new project."

### Access Restrictions
DM sees only own-portfolio projects. PM sees only own projects.

---

## Screen: Project Detail
**Route:** `/projects/:id`
**Audience:** Per role — see access matrix
**Layout:** Header section + tab navigation + tab content area.

### Components
- Project header: name, client (link), type badge, status badge, billing currency, DM, PM, edit button
- Status transition buttons (e.g., "Complete", "Put on Hold", "Cancel") — CEO, CTO, DM only
- Tabs: Assignments | Non-Human Costs (Phase 2) | Milestones (FP only, Phase 2) | Invoices (Phase 2) | Financials (restricted, Phase 2) | Worklogs (if enabled)

### Data Displayed (Header)

| Field | Source | Notes |
|---|---|---|
| All project fields | Project entity | |
| Contract Value | Project.contract_value | Phase 2 only; FP projects only |

### Actions
- Edit project → `/projects/:id/edit`
- Status transition → confirmation dialog → PUT /api/projects/:id/status
- Add Assignment (PM, DM) → opens assignment form
- Toggle worklog enabled (PM, DM)

### Empty State
Assignments tab: "No resources assigned yet. Add an assignment to get started."

### Access Restrictions
Financials tab: CEO, CTO, Finance only. Billing rates, billability_pct, is_shadow hidden from HR. Per `shared/ACCESS-MATRIX.md`.

---

## Screen: Project Create / Edit Form
**Route:** `/projects/new` and `/projects/:id/edit`
**Audience:** CEO, CTO, DM (create); CEO, CTO, DM, PM (edit)
**Layout:** Single-column form with conditional fields.

### Components
- Name input (required)
- Client dropdown (required) — from active clients
- Type radio/dropdown (required): Fixed Price / Time & Material / Client Onboarding
- Billing Currency dropdown (default INR)
- Start Date picker
- Contract End Date picker (required if T&M or Onboarding)
- DM dropdown (required) — from active resources
- PM dropdown (required) — from active resources
- Worklog Enabled toggle
- Notes textarea
- Save / Cancel buttons

### Actions
- Save → POST or PUT → redirect to project detail
- Cancel → back to project list

### Empty State
N/A.

### Access Restrictions
DM can only set themselves as DM when creating. CEO/CTO can assign any DM.
