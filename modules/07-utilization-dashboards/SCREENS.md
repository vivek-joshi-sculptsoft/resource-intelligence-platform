# Module 07: Utilization Dashboards — Screen Specifications

## Screen: Company Dashboard
**Route:** `/dashboard`
**Audience:** CEO, CTO
**Layout:** Grid of widgets, full-width.

### Components
- Billable Utilization % — large number widget with trend indicator
- Bench Count — count + expandable list of benched resources with days on bench
- Active Projects — count, breakdown by type (FP / T&M / Onboarding)
- Active Resources — count, allocated/bench breakdown
- Top 5 Projects by Team Size — table: Project Name, Team Size, Delivery Manager, Project Manager
- Overdue Milestones count + list
- Shadow Allocation — count of shadow assignments + total shadow allocation %
- Upcoming Releases — list of assignments ending in next 30 days

> **Removed (moved to Company Finance Dashboard below):** Total Monthly Revenue, Company Margin KPI cards, and the Revenue vs Cost widget. This screen no longer shows financial totals — see the dedicated finance screen for revenue/cost/margin with date-range filtering.

### Data Displayed

| Widget | Source | Formula |
|---|---|---|
| Billable Utilization % | Assignments | `shared/BUSINESS-RULES.md §7.1` Company Utilization |
| Bench Count | Resources with 0 ACTIVE assignments | |
| Active Projects by Type | Projects where status = ACTIVE | GROUP BY type |
| Top 5 Projects by Team Size | Projects + Assignments | `shared/BUSINESS-RULES.md §7.8` |
| Overdue Milestones | Milestones past planned_delivery_date | |
| Shadow Allocation | Assignments where is_shadow = true | |
| Upcoming Releases (30d) | Assignments with end_date in next 30 days | |

### Actions
- Click bench resource → Resource profile
- Click upcoming release → Assignment in project detail
- Click project type count → filtered project list
- Click a row in Top 5 Projects by Team Size → Project detail
- Click overdue milestone → Project detail (milestones tab)
- Hover/click info icon on each KPI card → tooltip with formula, meaning, and purpose (see Info Tooltips below)

### Info Tooltips

Every KPI card (`KpiCard` component) shows an info icon (`lucide-react` `Info`) next to its label. Hovering/clicking it opens a tooltip with three parts: **Formula**, **What it means**, **Why it matters**. Applies to all 4 KPI cards, the Shadow Allocation card heading, and the Top 5 Projects by Team Size card heading. Tooltip text shown to end users does not reference internal doc paths (e.g. `BUSINESS-RULES.md`) — those references are kept in this spec table only, for engineering traceability.

| Card | Formula | What it means | Why it matters |
|---|---|---|---|
| Billable Utilization % | `SUM(billable_pct) for non-shadow ACTIVE assignments / (active_resource_count × 100) × 100` — `shared/BUSINESS-RULES.md §7.1` | Share of total available capacity that is currently billed to clients | Core revenue-generating efficiency metric; low values mean idle/non-billable capacity |
| Bench Count | `COUNT(resources WHERE 0 ACTIVE assignments)` — `shared/BUSINESS-RULES.md §7.6` | Number of resources with no active project allocation | Drives bench cost exposure and signals resourcing/sales gaps |
| Active Projects | `COUNT(projects WHERE status = ACTIVE) GROUP BY type` | Number of currently active engagements, split by FP / T&M / Onboarding | Indicates current delivery load and engagement mix |
| Active Resources | `COUNT(resources WHERE is_active = true)`, with allocated/bench breakdown | Total headcount currently available for assignment | Denominator for utilization and capacity-planning metrics |
| Shadow Allocation | `COUNT(assignments WHERE is_shadow = true)`; allocation % = `SUM(billability_pct) for shadow assignments` | Number of shadow (non-billable) assignments and their share of total allocation | Shadow resources add cost but contribute no revenue — high values signal hidden cost exposure |
| Top 5 Projects by Team Size | `COUNT(DISTINCT resource_id) for ACTIVE assignments GROUP BY project_id, ORDER BY count DESC LIMIT 5` — `shared/BUSINESS-RULES.md §7.8` | The 5 currently active projects with the largest allocated headcount | Surfaces the org's biggest delivery commitments at a glance — where the most people (and risk) are concentrated |

### Empty State
Each widget shows "—" or "0" when no data. Top 5 Projects by Team Size shows "No active projects" when empty.

### Access Restrictions
CEO and CTO only.

---

## Screen: Company Finance Dashboard
**Route:** `/dashboard/finance`
**Audience:** CEO, CTO, Finance
**Layout:** Filter bar + KPI grid, full-width.

### Components
- Date range filter: **This Month** / **Last 3 Months** / **Custom** (custom shows start-date and end-date pickers)
- Project dropdown filter (single-select, searchable; default = all projects)
- Client dropdown filter (single-select, searchable; default = all clients)
- Total Revenue (Actual) — large number widget
- Total Projected Revenue — large number widget
- Total Cost (resource + non-human) — large number widget
- Company Margin — large number widget, projected and actual shown together (amount + %)

### Data Displayed

| Widget | Source | Formula |
|---|---|---|
| Total Revenue (Actual) | Invoices in selected period, optionally filtered by project/client | `shared/BUSINESS-RULES.md §7.4` |
| Total Projected Revenue | Assignments overlapping selected period, optionally filtered by project/client | `shared/BUSINESS-RULES.md §7.3a` |
| Total Cost | Resource + non-human costs in selected period, optionally filtered by project/client | `shared/BUSINESS-RULES.md §7.5a` |
| Company Margin | Projected and actual, amount + % | `shared/BUSINESS-RULES.md §7.5a` |

### Filter Behavior
- **This Month:** `period = [first day of current month, today]`
- **Last 3 Months:** `period = [first day of (current month − 2), today]`
- **Custom:** user picks `period.start` and `period.end`; `period.end` cannot be before `period.start`
- Project and Client filters narrow the same period-scoped aggregation (`project_id = :id` / `project.client_id = :id`); selecting a project auto-scopes the client dropdown to that project's client
- Filters combine with AND; changing any filter re-runs all four KPI calculations for the new scope

### Actions
- Hover/click info icon on each KPI card → tooltip with formula, meaning, and purpose (see Info Tooltips below)
- Change filter → re-fetch and re-render KPI grid

### Info Tooltips

Same `InfoTooltip` component and pattern as the Company Dashboard (`lucide-react` `Info` icon next to the label; Formula / What it means / Why it matters). Applies to all 4 KPI cards. Tooltip text shown to end users does not reference internal doc paths — those stay in this spec table for engineering traceability.

| Card | Formula | What it means | Why it matters |
|---|---|---|---|
| Total Revenue (Actual) | `SUM(invoice.amount_inr) WHERE status IN (APPROVED, PAID) AND invoice_date ∈ period` — `shared/BUSINESS-RULES.md §7.4` | Invoiced revenue actually recognized in the selected period | Source of truth for financial reporting; the number Finance reconciles against |
| Total Projected Revenue | `SUM(billability_pct/100 × working_days_in_period × 8 × billing_rate)` for non-shadow assignments overlapping the period — `shared/BUSINESS-RULES.md §7.3a` | Expected billable revenue from active assignments over the selected period | Forward-looking revenue signal; compare against actual to spot invoicing lag or shortfall |
| Total Cost | `Resource Cost (period) + Non-Human Cost (period)` — `shared/BUSINESS-RULES.md §7.5a` | Total cost to deliver — resource loaded cost plus non-human costs (licenses, infra, etc.) in the period | Denominator for margin; the full cost base leadership is accountable for |
| Company Margin | `(Revenue (period) − Total Cost (period)) / Revenue (period) × 100`, shown for both projected and actual — `shared/BUSINESS-RULES.md §7.5a` | Company-wide profitability after all resource and non-human costs, for the selected period/filters | Bottom-line profitability indicator — the headline number for this screen |

### Empty State
Each widget shows "—" when no assignments/invoices/costs fall in the selected period + filter combination.

### Access Restrictions
CEO, CTO, Finance only — gated on the `project_margin` data type (`shared/ACCESS-MATRIX.md`), scope `ALL`. DM's `OWN_PORTFOLIO` scope means DM does not see this company-wide screen (DM financials remain on the DM dashboard). PM, HR, Engineer: no access.

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
