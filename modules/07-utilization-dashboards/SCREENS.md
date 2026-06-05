# Module 07: Utilization Dashboards — Screen Specifications

## Screen: Company Dashboard
**Route:** `/dashboard`
**Audience:** CEO, CTO
**Layout:** Grid of widgets, full-width.

### Components
- Billable Utilization % — large number widget with trend indicator
- Bench Count — count + expandable list of benched resources with days on bench
- Shadow Allocation — count of shadow assignments + total shadow allocation %
- Active Projects — count, breakdown by type (FP / T&M / Onboarding)
- Upcoming Releases — list of assignments ending in next 30 days
- Overdue Milestones count (Phase 2)
- Revenue Summary: Projected vs Actual INR (Phase 2)
- Phase 2 financial widgets (cost, margin) — hidden in Phase 1

### Data Displayed

| Widget | Source | Formula |
|---|---|---|
| Billable Utilization % | Assignments | `shared/BUSINESS-RULES.md §7.1` Company Utilization |
| Bench Count | Resources with 0 ACTIVE assignments | |
| Shadow Allocation | Assignments where is_shadow = true | |
| Active Projects by Type | Projects where status = ACTIVE | GROUP BY type |
| Upcoming Releases (30d) | Assignments with end_date in next 30 days | |

### Actions
- Click bench resource → Resource profile
- Click upcoming release → Assignment in project detail
- Click project type count → filtered project list

### Empty State
Each widget shows "—" or "0" when no data.

### Access Restrictions
CEO and CTO only. Financial widgets (Phase 2) additionally restricted.

---

## Screen: Resource Availability View
**Route:** `/availability`
**Audience:** All roles including Engineer
**Layout:** Four sections (tabs or scroll sections): Bench | Partially Available | Releasing Soon | Fully Allocated

### Components
- 30 / 60 / 90 day filter tabs for "Releasing Soon" section
- Search by resource name
- Four sections with resource cards/rows

### Data Displayed (per FSD §9 Resource Availability View)

| Section | Fields Shown |
|---|---|
| Bench | Name, designation, expertise, days on bench, tags |
| Partial | Name, total allocation %, spare capacity %, project names |
| Releasing Soon | Name, project, allocation %, release date, days remaining |
| Fully Allocated | Name, total allocation %, project names |

### Actions
- Click resource name → Resource profile (if role has access)
- Click project name → Project detail (if role has access)

### Empty State
"No resources currently on bench." (per section)

### Access Restrictions
Project names and allocation % visible to all. Billing rates, billability %, CTC, shadow status NOT shown. Engineers see resource names and project names but NOT financial data.

---

## Screen: My Assignments (Engineer View)
**Route:** `/my-assignments`
**Audience:** Engineer only
**Layout:** List of active assignments + worklog entry section.

### Components
- Active assignments cards: project name, client, allocation %, start date, end date
- Worklog section (for projects with worklog_enabled = true) — defined in Module 11

### Data Displayed

| Field | Source | Notes |
|---|---|---|
| Project Name | Project.name | |
| Client | Client.name | |
| Allocation % | Assignment.allocation_pct | |
| Start Date | Assignment.start_date | |
| End Date | Assignment.end_date | "Ongoing" if null |

### Actions
- Click project → Project detail (read-only view of project name/client only — not full project page)
- Log hours (if worklog enabled) → Worklog module

### Empty State
"You have no active project assignments."

### Access Restrictions
Only own assignments. No billability, no shadow status, no billing rates.
