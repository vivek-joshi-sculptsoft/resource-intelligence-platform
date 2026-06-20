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
- Hover/click info icon on each KPI card → tooltip with formula, meaning, and purpose (see Info Tooltips below)

### Info Tooltips

Every KPI card (`KpiCard` component) shows an info icon (`lucide-react` `Info`) next to its label. Hovering/clicking it opens a tooltip with three parts: **Formula**, **What it means**, **Why it matters**. Applies to all 6 KPI cards (including Phase 2 cards, so the pattern is ready once their data lands) plus the Shadow Allocation card heading. Tooltip text shown to end users does not reference internal doc paths (e.g. `BUSINESS-RULES.md`) — those references are kept in this spec table only, for engineering traceability.

| Card | Formula | What it means | Why it matters |
|---|---|---|---|
| Billable Utilization % | `SUM(billable_pct) for non-shadow ACTIVE assignments / (active_resource_count × 100) × 100` — `shared/BUSINESS-RULES.md §7.1` | Share of total available capacity that is currently billed to clients | Core revenue-generating efficiency metric; low values mean idle/non-billable capacity |
| Bench Count | `COUNT(resources WHERE 0 ACTIVE assignments)` — `shared/BUSINESS-RULES.md §7.6` | Number of resources with no active project allocation | Drives bench cost exposure and signals resourcing/sales gaps |
| Active Projects | `COUNT(projects WHERE status = ACTIVE) GROUP BY type` | Number of currently active engagements, split by FP / T&M / Onboarding | Indicates current delivery load and engagement mix |
| Active Resources | `COUNT(resources WHERE is_active = true)`, with allocated/bench breakdown | Total headcount currently available for assignment | Denominator for utilization and capacity-planning metrics |
| Total Monthly Revenue (Phase 2) | `SUM(per-assignment projected revenue) for non-shadow ACTIVE assignments` — `shared/BUSINESS-RULES.md §7.3` | Projected billable revenue for the current month across all active assignments | Top-line financial health indicator |
| Company Margin (Phase 2) | `Projected Revenue (INR) − Total Project Cost` — `shared/BUSINESS-RULES.md §7.5` | Company-wide projected margin after resource and non-human costs | Bottom-line profitability indicator after costs |
| Shadow Allocation | `COUNT(assignments WHERE is_shadow = true)`; allocation % = `SUM(billability_pct) for shadow assignments` | Number of shadow (non-billable) assignments and their share of total allocation | Shadow resources add cost but contribute no revenue — high values signal hidden cost exposure |

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
