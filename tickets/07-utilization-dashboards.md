# Module 07: Utilization Dashboards — JIRA Tickets

---

## Story: Implement Company Dashboard aggregation API
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 01-auth-and-roles, 04-resource-management, 03-project-management, 05-allocation-tracking
**Labels:** backend

### Description
Build GET /api/dashboard/company returning company-wide aggregated metrics. Phase 1 metrics: billable_utilization_pct (using shared/BUSINESS-RULES.md section 7.1 formula: SUM all billable allocation / active_resource_count * 100), total_active_resources, bench_count with bench_resources list (name, designation, days_on_bench), shadow_count and shadow_total_allocation_pct, active_project_count with breakdown by type, and upcoming_releases_30d (assignments with end_date in next 30 days). Phase 2 fields (overdue_milestones, projected_revenue_inr, actual_revenue_inr, total_cost_inr) return null in Phase 1. Restricted to CEO and CTO only.

### Acceptance Criteria
- [ ] billable_utilization_pct calculated per BUSINESS-RULES.md section 7.1: SUM(billability_pct where is_shadow=false) / (active_resource_count * 100) * 100
- [ ] total_active_resources = count of resources with is_active=true
- [ ] bench_count = count of active resources with 0 ACTIVE assignments
- [ ] bench_resources list includes name, designation, days_on_bench (calculated from last released_at or date_of_joining)
- [ ] shadow_count = count of ACTIVE assignments where is_shadow=true
- [ ] shadow_total_allocation_pct = SUM(allocation_pct) where is_shadow=true
- [ ] active_project_count with breakdown: FIXED_PRICE, TIME_AND_MATERIAL, CLIENT_ONBOARDING
- [ ] upcoming_releases_30d: assignments with end_date in next 30 days (resource_name, project_name, end_date, days_remaining)
- [ ] Phase 2 fields return null
- [ ] CEO and CTO only — 403 for all other roles

---

## Story: Implement DM Dashboard aggregation API
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** Company Dashboard API
**Labels:** backend

### Description
Build GET /api/dashboard/dm returning portfolio-level metrics for a Delivery Manager. Metrics: portfolio_utilization_pct (utilization formula scoped to DM's projects), active_project_count (DM's projects with status=ACTIVE), resource_count (distinct resources on DM's projects), bench_count (DM portfolio resources with 0% allocation), upcoming_releases_30d (scoped to DM's projects). Phase 2 adds delivery_delays, projected_revenue_inr, total_cost_inr. Accessible to DM (OWN_PORTFOLIO), CEO, CTO.

### Acceptance Criteria
- [ ] portfolio_utilization_pct calculated for DM's projects only
- [ ] active_project_count = count of DM's projects with status=ACTIVE
- [ ] resource_count = distinct resources assigned to DM's projects
- [ ] bench_count = DM portfolio resources with 0% total allocation
- [ ] upcoming_releases_30d scoped to DM's projects
- [ ] Phase 2 fields (delivery_delays, projected_revenue_inr, total_cost_inr) return null
- [ ] DM sees own portfolio only (dm_id = current user)
- [ ] CEO and CTO can view any DM's dashboard (or aggregated)

---

## Story: Implement Resource Availability API visible to all roles
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 04-resource-management, 05-allocation-tracking
**Labels:** backend

### Description
Build GET /api/dashboard/availability returning resource availability categorized into four groups. Bench: resources with 0 ACTIVE assignments (name, designation, expertise, days_on_bench, tags). Partial: resources with total allocation < 100% (name, total_allocation_pct, spare_capacity_pct, project names). Releasing soon: resources with ACTIVE assignments ending within a window (name, project, allocation_pct, end_date, days_remaining) — supports ?window=30|60|90 filter. Fully allocated: resources with total allocation >= 100% (name, total_allocation_pct, project names). This endpoint is accessible to ALL authenticated roles including Engineer. Financial fields (billing_rate, billability_pct, CTC, shadow status) are excluded from the response for all roles.

### Acceptance Criteria
- [ ] bench: active resources with 0 ACTIVE assignments — name, designation, expertise, days_on_bench, tags
- [ ] partial: active resources with 0 < total_allocation < 100% — name, total_allocation_pct, spare_capacity_pct, project names
- [ ] releasing_soon: resources with end_date within window — name, project_name, allocation_pct, end_date, days_remaining
- [ ] fully_allocated: active resources with total_allocation >= 100% — name, total_allocation_pct, project names
- [ ] ?window=30|60|90 filter for releasing_soon (default 30)
- [ ] Accessible to ALL authenticated roles including Engineer
- [ ] No billing_rate, billability_pct, loaded_cost_monthly, or is_shadow in response
- [ ] days_on_bench calculated correctly from last released_at or date_of_joining

---

## Story: Implement Client Dashboard aggregation API
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** 02-client-management, 05-allocation-tracking
**Labels:** backend

### Description
Build GET /api/clients/:clientId/dashboard (or integrate into existing client detail endpoint). Phase 1 metrics: active_resource_count (count of distinct resources with ACTIVE assignments on the client's projects), active_project_count (projects with status=ACTIVE), project_count_by_type. Phase 2 adds total_monthly_billing_inr, total_cost_inr, aggregate_margin_inr, aggregate_margin_pct. Access follows client_profiles rules from the access matrix.

### Acceptance Criteria
- [ ] active_resource_count = distinct resources with ACTIVE assignments on client's projects
- [ ] active_project_count = count of client's ACTIVE projects
- [ ] project_count_by_type = { FIXED_PRICE: int, TIME_AND_MATERIAL: int, CLIENT_ONBOARDING: int }
- [ ] Phase 2 financial fields return null
- [ ] Same access control as client detail endpoint
- [ ] Financial metrics (Phase 2) restricted to CEO, CTO, Finance, DM (configurable)

---

## Story: Implement Project Financials API stub for Phase 2
**Type:** Task
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P3
**Estimate:** S (1-2d)
**Depends On:** 03-project-management
**Labels:** backend

### Description
Build GET /api/projects/:projectId/financials endpoint as a stub that returns all financial fields as null in Phase 1. Fields: resource_cost_inr, non_human_cost_inr, total_cost_inr, projected_revenue_inr, actual_revenue_inr, projected_margin_inr, projected_margin_pct, actual_margin_inr, actual_margin_pct. Restricted to CEO, CTO, Finance (EDIT ALL), and DM (OWN_PORTFOLIO, configurable). This stub ensures the API contract is established and the frontend can build against it.

### Acceptance Criteria
- [ ] All 9 financial fields returned as null in Phase 1
- [ ] Access control: CEO, CTO, Finance have access; DM own portfolio (configurable); PM/HR/Engineer 403
- [ ] Response shape matches the Phase 2 specification
- [ ] Endpoint is documented and versioned

---

## Story: Build Company Dashboard screen with widgets
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** Company Dashboard API, DM Dashboard API
**Labels:** frontend

### Description
Create the /dashboard page (landing page for CEO/CTO) with a grid of widgets. Widgets: Billable Utilization % (large number with trend indicator), Bench Count (count + expandable list with days on bench), Shadow Allocation (count + total %), Active Projects (count + breakdown by type FP/T&M/Onboarding), Upcoming Releases (list of assignments ending in next 30 days). Phase 2 financial widgets (Overdue Milestones, Revenue Summary, Cost, Margin) are hidden in Phase 1. Each widget is interactive: clicking bench resource navigates to their profile, clicking upcoming release navigates to project detail, clicking project type count navigates to filtered project list.

### Acceptance Criteria
- [ ] Billable Utilization % widget with large number display
- [ ] Bench Count widget with expandable list (name, designation, days on bench) — click navigates to resource profile
- [ ] Shadow Allocation widget: count + total allocation %
- [ ] Active Projects widget: count + breakdown by type — click type navigates to filtered project list
- [ ] Upcoming Releases widget: list with resource_name, project_name, end_date, days_remaining — click navigates to project detail
- [ ] Phase 2 financial widgets hidden/placeholder in Phase 1
- [ ] Each widget shows "0" or "--" when no data
- [ ] CEO and CTO only — other roles see a different landing page or 403

---

## Story: Build Resource Availability screen visible to all roles
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P0
**Estimate:** L (5-10d)
**Depends On:** Resource Availability API
**Labels:** frontend

### Description
Create the /availability page with four sections (tabs or scroll sections): Bench (resources with 0% allocation — name, designation, expertise, days on bench, tags), Partially Available (0 < allocation < 100% — name, total allocation %, spare capacity %, project names), Releasing Soon (end_date within window — name, project, allocation %, release date, days remaining with 30/60/90 day filter tabs), and Fully Allocated (allocation >= 100% — name, total allocation %, project names). Include search by resource name. No billing rates, billability %, CTC, or shadow status shown. All roles including Engineer can access this page. Clicking resource name navigates to profile (if role has access); clicking project name navigates to project detail (if role has access).

### Acceptance Criteria
- [ ] Bench section: name, designation, expertise, days on bench, tags
- [ ] Partial section: name, total allocation %, spare capacity %, project names
- [ ] Releasing Soon section: name, project, allocation %, release date, days remaining
- [ ] 30 / 60 / 90 day filter tabs for Releasing Soon
- [ ] Fully Allocated section: name, total allocation %, project names
- [ ] Search by resource name across all sections
- [ ] No billing_rate, billability_pct, loaded_cost_monthly, or is_shadow displayed
- [ ] All roles including Engineer can access
- [ ] Click resource name navigates to /resources/:id (if role has access)
- [ ] Click project name navigates to /projects/:id (if role has access)
- [ ] Empty state per section: "No resources currently on bench." etc.

---

## Story: Build My Assignments screen for Engineer role
**Type:** Feature
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** 05-allocation-tracking (resource assignments API)
**Labels:** frontend

### Description
Create the /my-assignments page for Engineer role showing their active assignment cards: project name, client name, allocation %, start date, end date ("Ongoing" if null). No billability, shadow status, or billing rate shown. Include a worklog section placeholder for projects with worklog_enabled=true (implemented in Module 11). Empty state: "You have no active project assignments."

### Acceptance Criteria
- [ ] Assignment cards: project name, client name, allocation %, start date, end date
- [ ] End date shows "Ongoing" if null
- [ ] No billability_pct, is_shadow, or billing_rate displayed
- [ ] Worklog section placeholder for projects with worklog_enabled=true
- [ ] Empty state: "You have no active project assignments."
- [ ] Only Engineer's own assignments shown (SELF_ONLY scope)
- [ ] Click project name shows project name/client only (not full project detail page)

---

## Story: Implement dashboard performance optimization with query efficiency
**Type:** Task
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P2
**Estimate:** M (3-5d)
**Depends On:** All dashboard APIs
**Labels:** backend, infrastructure

### Description
Optimize all dashboard aggregation queries for performance. The company dashboard, DM dashboard, availability view, and client dashboard all involve aggregating across multiple tables (assignments, resources, projects). Ensure queries use appropriate indexes, avoid N+1 patterns, use database-level aggregation (GROUP BY, COUNT, SUM) rather than application-level loops, and consider response caching for expensive computations (company-wide utilization). The target is sub-500ms response time for the company dashboard with up to 40 resources and 50 projects.

### Acceptance Criteria
- [ ] All dashboard queries use database-level aggregation (no N+1 queries)
- [ ] Existing indexes on assignment.status, assignment.resource_id, assignment.project_id, resource.is_active leveraged
- [ ] Company dashboard responds in < 500ms with 40 resources and 50 projects
- [ ] Consider short-TTL cache for company-wide utilization computation
- [ ] No post-fetch filtering — all scope filtering at DB level
- [ ] Query execution plans reviewed for all dashboard endpoints

---

## Story: Write tests for dashboard aggregation correctness and access control
**Type:** Task
**Phase:** 1
**Module:** 07-utilization-dashboards
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** All dashboard APIs
**Labels:** backend

### Description
Write tests covering: company dashboard metric correctness (utilization formula, bench count, shadow count, project breakdown, upcoming releases), DM dashboard scoping (only own portfolio projects), resource availability categorization (bench, partial, releasing soon, fully allocated), client dashboard correctness, days_on_bench calculation, access control (company dashboard CEO/CTO only, DM dashboard scoped, availability view all roles), and Phase 2 fields returning null.

### Acceptance Criteria
- [ ] Company utilization formula: verified with known inputs per BUSINESS-RULES.md section 7.1
- [ ] Bench count: correctly identifies resources with 0 ACTIVE assignments
- [ ] Bench days: correctly calculated from last released_at or date_of_joining
- [ ] Shadow metrics: correct count and total allocation %
- [ ] Project breakdown by type: correct counts
- [ ] Upcoming releases: correctly identifies assignments ending in 30 days
- [ ] DM dashboard: shows only own portfolio metrics (dm_id = self)
- [ ] Availability: bench, partial, releasing_soon, fully_allocated categories correct
- [ ] Availability 30/60/90 day filter works correctly
- [ ] Client dashboard: correct resource and project counts
- [ ] Access control: company dashboard 403 for non-CEO/CTO; availability accessible to all roles
- [ ] Phase 2 financial fields return null
