# Module 02: Client Management — Screen Specifications

## Screen: Client List
**Route:** `/clients`
**Audience:** CEO, CTO, DM, PM, Finance, HR (Engineer has no access)
**Layout:** Full-width table with header action bar.

### Components
- Client table: name, industry, engagement start date, active project count, status
- "Add Client" button (visible to CEO, CTO only)
- Status filter: Active / Inactive / All
- Search input: search by client name
- Column sort: name, engagement_start_date

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Name | Client.name | Clickable link to detail |
| Industry | Client.industry | |
| Engagement Start | Client.engagement_start_date | Formatted date |
| Active Projects | Computed | Count of projects with status=ACTIVE |
| Status | Client.is_active | Active / Inactive badge |

### Actions
- Click row → Client detail page
- Add Client → `/clients/new` (CEO, CTO only)

### Empty State
"No clients found. Add your first client to get started."

### Access Restrictions
Engineer role sees no clients screen. DM/PM see only clients for their portfolio.

---

## Screen: Client Detail
**Route:** `/clients/:id`
**Audience:** CEO, CTO, DM (own portfolio), PM (own portfolio), Finance, HR
**Layout:** Header info + dashboard stats row + projects table.

### Components
- Client header: name, industry, contact info, engagement start, notes, edit button
- Phase 1 dashboard row: active resources count, active projects count
- Phase 2 dashboard row (added later): total billing INR, total cost INR, aggregate margin
- Projects table: name, type, status, DM name, PM name, link to project detail
- Edit button (CEO, CTO only)

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| All client fields | Client entity | |
| Active Resource Count | Dashboard endpoint | Count of distinct resources on active projects |
| Active Project Count | Dashboard endpoint | |
| Projects | Project list for this client | Name, type (badge), status (badge), DM, PM |
| Financial metrics | Dashboard endpoint | Phase 2 only; null/hidden in Phase 1 |

### Actions
- Edit client → `/clients/:id/edit` (CEO, CTO only)
- Click project → `/projects/:id`
- Deactivate client (CEO, CTO) → confirmation dialog → DELETE /api/clients/:id

### Empty State
Projects table: "No projects yet. Add a project for this client."

### Access Restrictions
Financial metrics (billing, cost, margin) visible only to CEO, CTO, Finance per `shared/ACCESS-MATRIX.md`.

---

## Screen: Client Create / Edit Form
**Route:** `/clients/new` and `/clients/:id/edit`
**Audience:** CEO, CTO only
**Layout:** Single-column form.

### Components
- Name input (required)
- Industry input
- Contact Name input
- Contact Email input
- Contact Phone input
- Engagement Start Date picker
- Notes textarea
- Save / Cancel buttons

### Actions
- Save → POST (create) or PUT (edit) → redirect to client detail on success
- Cancel → back to client list

### Empty State
N/A.

### Access Restrictions
Create/edit forms visible to CEO and CTO only.
