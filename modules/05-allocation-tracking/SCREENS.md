# Module 05: Allocation Tracking — Screen Specifications

## Screen: Assignment List (within Project Detail)
**Route:** `/projects/:id` → Assignments tab
**Audience:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance, HR (limited)
**Layout:** Table within the project detail tab area.

### Components
- Assignment table (see data below)
- "Add Assignment" button (PM, DM, CEO, CTO)
- Status filter: Active / Released / All
- Over-allocation banner (shown when any resource is over-allocated)

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Resource Name | Resource.name | Link to resource profile |
| Effective Designation | project_designation ?? resource.designation | Designation resolution applied |
| Effective Expertise | project_expertise ?? resource.technical_expertise | |
| Allocation % | Assignment.allocation_pct | |
| Billability % | Assignment.billability_pct | Hidden from HR, Engineer |
| Shadow | Assignment.is_shadow | Shown as badge; hidden from HR, Engineer |
| Billing Rate | Assignment.billing_rate | Phase 2 only; restricted per access matrix |
| Start Date | Assignment.start_date | |
| End Date | Assignment.end_date | "Ongoing" if null |
| Status | Assignment.status | Badge: Active / Released / Auto-Released |

### Actions
- Add Assignment → assignment create form (modal or slide-over)
- Click assignment row → edit form
- Release button on active assignment → confirmation dialog → POST /api/assignments/:id/release

### Empty State
"No assignments yet. Add a resource to this project."

### Access Restrictions
`billability_pct`, `is_shadow`, `billing_rate` hidden from HR and Engineer. Per `shared/ACCESS-MATRIX.md`.

---

## Screen: Assignment Create / Edit Form
**Route:** Modal/slide-over within `/projects/:id`
**Audience:** CEO, CTO, DM (own portfolio), PM (own portfolio)
**Layout:** Form in modal or slide-over panel.

### Components
- Resource dropdown (required) — active resources with current total allocation shown
- Allocation % input (required, 1–100)
- Billability % input (required, 0–100)
- Shadow toggle — when enabled, billability auto-set to 0 and disabled
- Project Designation override input (optional)
- Project Expertise override input (optional)
- Billing Rate input (Phase 2 only — visible to authorized roles)
- Start Date picker (required)
- End Date picker (optional — "Ongoing" if blank)
- Over-allocation warning banner (shown inline when total would exceed 100%)

### Validation Messages
- "Billability cannot exceed allocation percentage"
- "Shadow resources cannot have billability"
- "End date must be after start date"
- "Resource already has an active assignment on this project"
- "Cannot create assignment on a non-active project"
- "Allocation must be between 1% and 100%"
- Warning: "This will bring total allocation to {X}%" (non-blocking)

### Actions
- Save → POST (create) or PUT (edit)
- Cancel → close form

### Empty State
N/A.

---

## Screen: Resource Assignments Panel (within Resource Profile)
**Route:** `/resources/:id` → Assignments section
**Audience:** CEO, CTO, DM, PM, HR; Engineer (self only)
**Layout:** Section or tab within resource profile.

### Components
- Active assignments table: project name, effective designation, allocation %, billability %, shadow, start/end date
- Total allocation % indicator (highlighted red if > 100%)
- Assignment history (expandable): released/auto-released assignments with dates

### Data Displayed
Same as assignment list but scoped to one resource. `billability_pct` and `is_shadow` follow access restrictions.

### Actions
None — read-only from resource profile. Assignment edits are done from the project detail page.

### Empty State
"No active assignments. This resource is currently on bench."
