# Module 11: Worklog — Screen Specifications

## Screen: Worklog Entry (My Assignments View)
**Route:** `/my-assignments` — Worklog section (only for projects with `worklog_enabled = true`)
**Audience:** Any user with an active assignment on a worklog-enabled project
**Layout:** Card per project or inline form.

### Components
- Project selector (pre-populated from active assignments where worklog_enabled = true)
- Date picker (defaults to today; cannot select future dates)
- Hours input (0.5–24.0 in 0.5 increments; spinner or dropdown)
- Note textarea (optional)
- "Log Hours" / "Save" button

### Data Displayed
- Active project list (with worklog_enabled = true)
- Recent entries for current user: last 30 days table (date, project, hours, note, edit button)

### Validation Messages
- "Worklog is not enabled for this project"
- "You must have an active assignment to log hours"
- "Cannot log hours for future dates"
- "Hours must be between 0.5 and 24"
- "Entry already exists for this date. Edit the existing entry."

### Actions
- Submit → POST /api/worklogs → update recent entries
- Edit existing → PUT /api/worklogs/:id
- Delete entry → DELETE /api/worklogs/:id (with confirmation)
- Export (Recent Entries table) → GET /api/worklogs/my/export → downloads .xlsx of the currently visible entries

### Empty State
If no worklog-enabled projects: "No projects with worklog enabled. Ask your manager to enable worklog for your project."

### Access Restrictions
Only logs for own resource. Cannot see other resources' worklogs.

---

## Screen: Worklog Tab (within Project Detail)
**Route:** `/projects/:id` → Worklogs tab (shown only when `worklog_enabled = true`)
**Audience:** CEO, CTO, FINANCE, HR (all), DM (own portfolio), PM (own portfolio)
**Layout:** Table with filters above.

### Components
- Date range filter (start/end)
- Resource filter dropdown (all resources on this project)
- Worklog table

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Date | Worklog.log_date | Formatted date |
| Resource | Resource.name | |
| Hours | Worklog.hours | |
| Note | Worklog.note | Truncated with expand |

### Actions
- Filter by date range or resource
- Export → GET /api/projects/:id/worklogs/export → downloads .xlsx of the currently filtered entries (date range + resource)

### Empty State
"No worklog entries for this period."

### Access Restrictions
Manager view only. Engineers view their own entries via `/my-assignments` not this tab.

---

## Screen: Worklogs (Company-Wide View)
**Route:** `/worklogs`
**Audience:** CEO, CTO, FINANCE, HR (all); DM/PM (own portfolio); ENGINEER (own entries only). Previously implemented but not documented in this file — added here alongside the Export feature.
**Layout:** Table with filters above, paginated.

### Components
- Date range filter (start/end)
- Worklog table
- Export button

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Date | Worklog.log_date | Formatted date |
| Resource | Resource.name | Avatar + name |
| Project | Project.name | |
| Hours | Worklog.hours | |
| Notes | Worklog.note | Truncated with expand |

### Actions
- Filter by date range
- Export → GET /api/worklogs/export → downloads .xlsx of the currently filtered entries

### Empty State
"No worklog entries found."

### Access Restrictions
Per `shared/ACCESS-MATRIX.md` (`worklogs`) scope for the current role.

---

## Screen: Worklog History (My Worklog)
**Route:** `/my-worklogs`
**Audience:** Any logged-in user with a resource_id
**Layout:** Table with date and project filters.

### Components
- Date range filter
- Project filter
- Worklog table: date, project, hours, note, edit/delete buttons

### Actions
- Edit entry → inline or modal
- Delete entry → confirmation dialog

### Empty State
"No worklog entries found."
