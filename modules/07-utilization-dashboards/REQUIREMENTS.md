# Module 07: Utilization Dashboards

## Overview

Dashboards provide at-a-glance visibility at every level. All metrics are derived from live allocation and billability data. This module owns no new entities — it reads from Assignment, Resource, Project, Invoice, and NonHumanCost. Phase 1 provides utilization and availability metrics; Phase 2 adds financial widgets (revenue, cost, margin).

## Phase

Phase 1 (utilization metrics only). Phase 2 adds financial widgets.

## Dependencies

- Module 01 (Auth & Roles)
- Module 04 (Resource Management) — resource data
- Module 03 (Project Management) — project data
- Module 05 (Allocation Tracking) — assignment data
- Module 08 (Financial Engine) — Phase 2 financial widgets
- Module 09 (Invoicing) — Phase 2 revenue data
- Module 06 (Non-Human Costs) — Phase 2 cost data

---

## Features

### Feature: Company-Wide Dashboard
**Description:** Aggregate metrics for the entire organization. Visible to CEO and CTO. No revenue/cost/margin totals — see Company Finance Dashboard below.
**Acceptance Criteria:**
- [ ] Billable utilization % (§7.1 Company Utilization formula)
- [ ] Bench count (resources with 0 ACTIVE assignments) with names
- [ ] Shadow allocation count and total % (SUM allocation_pct where is_shadow = true)
- [ ] Active project count by type
- [ ] Top 5 projects by team size: project name, team size, DM, PM (§7.8 formula)
- [ ] Upcoming releases: assignments with end_date in next 30 days
- [ ] Overdue milestones count + list
- [ ] Info tooltip (formula, meaning, why it matters) on each KPI card, Shadow Allocation, and Top 5 Projects by Team Size — `InfoTooltip` pattern, no regressions from prior tooltip coverage

### Feature: Company Finance Dashboard
**Description:** Company-wide revenue, cost, and margin with date-range filtering. Visible to CEO, CTO, Finance only.
**Acceptance Criteria:**
- [ ] Date range filter: This Month / Last 3 Months / Custom (start + end date)
- [ ] Project dropdown filter (optional, single-select)
- [ ] Client dropdown filter (optional, single-select)
- [ ] Total Revenue (Actual) for selected period + filters (§7.4)
- [ ] Total Projected Revenue for selected period + filters (§7.3a)
- [ ] Total Cost (resource + non-human) for selected period + filters (§7.5a)
- [ ] Company Margin — projected and actual, amount + % (§7.5a)
- [ ] Custom range validation: end_date >= start_date
- [ ] Info tooltip (formula, meaning, why it matters) on each of the 4 KPI cards — same `InfoTooltip` pattern as Company Dashboard
- [ ] Access restricted to CEO/CTO/Finance (`project_margin` data type, scope ALL); DM/PM/HR/Engineer get 403 or no nav entry

### Feature: DM-Level Dashboard
**Description:** Aggregate metrics for a DM's portfolio.
**Acceptance Criteria:**
- [ ] Utilization % for DM's projects
- [ ] Resource availability for DM's portfolio
- [ ] Delivery delays visible
- [ ] Scoped to `dm_id = current user` for DM role

### Feature: Client-Level Dashboard
**Description:** Consolidated view within client detail page.
**Acceptance Criteria:**
- [ ] Total active resources deployed on client's projects
- [ ] Active project count
- [ ] Phase 2: total monthly billing INR, total cost INR, aggregate margin, project breakdown by type

### Feature: Project-Level Dashboard (within Project Detail)
**Description:** Per-project metrics in the project detail view.
**Acceptance Criteria:**
- [ ] Resource list with allocation %, billability %, shadow flag
- [ ] Phase 2: resource cost + non-human cost vs revenue, margins

### Feature: Individual Resource Dashboard (within Resource Profile)
**Description:** Per-resource utilization and history.
**Acceptance Criteria:**
- [ ] Total allocation % across all projects
- [ ] Billability breakdown (billable vs shadow)
- [ ] Assignment history timeline
- [ ] Upcoming release date if end_date set

### Feature: Resource Availability View
**Description:** Standalone page visible to ALL users including engineers.
**Acceptance Criteria:**
- [ ] Currently on bench: name, designation, expertise, days on bench, tags
- [ ] Partially available: name, total allocation %, spare capacity %, project names
- [ ] Releasing soon: name, project, allocation %, release date, days remaining (30/60/90 day filters)
- [ ] Fully allocated: name, total allocation %, project names
- [ ] Billing rates, billability %, CTC, shadow status NOT visible to engineers

---

## Validations

No entity writes — read-only aggregations. No validations required.

---

## Business Rules

All calculations from `shared/BUSINESS-RULES.md`:
- Company utilization: §7.1 formula
- Project cost: §7.2 formula
- Projected revenue (current month): §7.3 formula
- Projected revenue (date range): §7.3a formula — Company Finance Dashboard
- Actual revenue: §7.4 formula
- Margin (current month): §7.5 formula
- Margin (date range): §7.5a formula — Company Finance Dashboard
- Bench cost: §7.6 formula
- Exchange rate conversion: §7.7 formula
- Team size ranking: §7.8 formula — Company Dashboard "Top 5 Projects" widget

Access: dashboard data filtered by role scope per `shared/ACCESS-MATRIX.md`. Financial data (cost, margin, billing) restricted to CEO/CTO/Finance; configurable for DM. Company Finance Dashboard specifically requires scope `ALL` on `project_margin`, so DM (scope `OWN_PORTFOLIO`) does not see it.
