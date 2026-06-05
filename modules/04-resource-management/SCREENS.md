# Module 04: Resource Management — Screen Specifications

## Screen: Resource List
**Route:** `/resources`
**Audience:** CEO, CTO, DM, PM, Finance, HR, Engineer (limited)
**Layout:** Full-width table with filter sidebar or filter bar.

### Components
- Search input: by name or employee ID
- Filters: designation, expertise, tags (multi-select), availability (Bench / Partial / Fully Allocated / All)
- Status filter: Active / Inactive / All
- "Add Resource" button (CEO, CTO, HR only)
- Resource table with column sort

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Name | Resource.name | Link to profile |
| Employee ID | Resource.employee_id | |
| Designation | Resource.designation | |
| Expertise | Resource.technical_expertise | |
| Tags | ResourceTag | Pill badges |
| Total Allocation % | Computed | Sum of ACTIVE assignment allocation_pct |
| Availability | Computed | Bench (0%) / Partial (<100%) / Full (100%+) |
| Status | Resource.is_active | Active / Inactive |

### Actions
- Click row → Resource profile
- Add Resource → `/resources/new`

### Empty State
"No resources found. Try adjusting filters."

### Access Restrictions
Engineer sees only own record. `loaded_cost_monthly` never shown in list view.

---

## Screen: Resource Profile
**Route:** `/resources/:id`
**Audience:** Per role — CEO/CTO/DM/PM/Finance/HR (broad); Engineer (self only)
**Layout:** Header + stats row + tabs.

### Components
- Header: name, employee ID, designation, expertise, date of joining, reporting manager, tags, edit button
- Stats row: total allocation %, availability status, days on bench (if 0%)
- Active Assignments table (tab or section)
- Assignment history table
- Loaded Cost field (CEO/CTO/Finance only, Phase 2)
- Edit button (CEO/CTO/HR for profiles; CEO/CTO/Finance for cost)

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| All resource fields | Resource entity | |
| Loaded Cost | Resource.loaded_cost_monthly | Phase 2; null/hidden for unauthorized roles |
| Tags | ResourceTag | Editable tag list |
| Active Assignments | Assignment + Project | Project name, project designation (with fallback), allocation %, billability % (hidden from HR/Engineer), shadow flag (hidden from HR/Engineer), rate, start/end date |
| Total Allocation % | Computed | Highlighted red if > 100% |

### Actions
- Edit profile → `/resources/:id/edit`
- Add/remove tags → inline or modal
- View assignment history → expandable section or separate tab

### Empty State
Assignments section: "No active assignments. This resource is on bench."

### Access Restrictions
`loaded_cost_monthly`, `billing_rate`, `billability_pct`, `is_shadow` fields hidden from HR and Engineer per `shared/ACCESS-MATRIX.md`.

---

## Screen: Resource Create / Edit Form
**Route:** `/resources/new` and `/resources/:id/edit`
**Audience:** CEO, CTO, HR (create/edit); Finance (edit loaded_cost_monthly only, Phase 2)
**Layout:** Single-column form.

### Components
- Name input (required)
- Employee ID input (required)
- Designation input (required)
- Technical Expertise input
- Date of Joining date picker
- Reporting Manager dropdown — from active resources
- Tags input with add/remove
- Loaded Cost (monthly INR) input — Phase 2, visible to CEO/CTO/Finance only
- Save / Cancel buttons

### Actions
- Save → POST or PUT → redirect to resource profile
- Cancel → back to resource list

### Empty State
N/A.

### Access Restrictions
Loaded cost field shown only to CEO, CTO, Finance. Tag management available to CEO, CTO, HR.
