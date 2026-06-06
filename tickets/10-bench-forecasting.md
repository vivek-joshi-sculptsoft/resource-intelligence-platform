# Module 10: Bench & Availability Forecasting -- JIRA Tickets

---

## Story: Build current bench list aggregation API
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 04-resource-management, 05-allocation-tracking
**Labels:** backend

### Description
Implement `GET /api/bench` to list all resources currently on bench (0 ACTIVE assignments). Returns resource profile info, days on bench, bench start date, and tags. Bench start = max(released_at) of last assignment, or date_of_joining if never assigned. Phase 2 adds bench cost fields (daily_bench_cost_inr, total_bench_cost_inr) which are null in Phase 1 and restricted to CEO/CTO/Finance. Visible to all authenticated roles.

### Acceptance Criteria
- [ ] Returns all resources with 0 ACTIVE assignments
- [ ] Each entry shows: id, name, designation, technical_expertise, tags, days_on_bench, bench_start_date
- [ ] Bench start = max(released_at) of last assignment, or date_of_joining if never assigned
- [ ] days_on_bench computed from bench_start_date to today
- [ ] daily_bench_cost_inr and total_bench_cost_inr returned as null in Phase 1
- [ ] Visible to all authenticated roles
- [ ] Only active resources included (is_active = true)
- [ ] Unit tests for bench start calculation (last released, never assigned, multiple assignments)

---

## Story: Build bench summary aggregation API
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 10-bench-forecasting (bench list API)
**Labels:** backend

### Description
Implement `GET /api/bench/summary` for the company dashboard widget. Returns bench_count, list of benched resource names with days_on_bench, and total_bench_cost_inr (null in Phase 1, restricted in Phase 2). Visible to all authenticated roles; cost fields restricted to CEO/CTO/Finance.

### Acceptance Criteria
- [ ] Returns bench_count (number of benched resources)
- [ ] Returns resources array with name and days_on_bench
- [ ] total_bench_cost_inr returned as null in Phase 1
- [ ] Visible to all authenticated roles
- [ ] Cost fields return null for unauthorized roles (even in Phase 2)
- [ ] Unit tests for summary aggregation

---

## Story: Build upcoming availability API with configurable window
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 05-allocation-tracking, 04-resource-management
**Labels:** backend

### Description
Implement `GET /api/availability/upcoming` to list resources whose assignments end within a configurable window (30/60/90 days, default 30). Returns resource info, project name, allocation percentage, end date, and days remaining. Only includes assignments with an end_date set (auto-release aware). Visible to all authenticated roles.

### Acceptance Criteria
- [ ] Returns resources with ACTIVE assignments ending within the specified window
- [ ] Supports `?window=30|60|90` query parameter, default 30
- [ ] Each entry shows: resource (id, name, designation), project (id, name), allocation_pct, end_date, days_remaining
- [ ] Only includes assignments with end_date set (excludes open-ended)
- [ ] days_remaining computed from today to end_date
- [ ] Visible to all authenticated roles
- [ ] Unit tests for each window size and edge cases (end_date = today, end_date = boundary)

---

## Story: Build partial availability API
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 05-allocation-tracking, 04-resource-management
**Labels:** backend

### Description
Implement `GET /api/availability/partial` to list resources with at least one ACTIVE assignment but total allocation < 100%. Returns resource info, total allocation percentage, spare capacity, and current project names. Visible to all authenticated roles.

### Acceptance Criteria
- [ ] Returns resources with at least one ACTIVE assignment and total_allocation_pct < 100
- [ ] Each entry shows: id, name, designation, total_allocation_pct, spare_capacity_pct, projects array
- [ ] spare_capacity_pct = 100 - total_allocation_pct
- [ ] Visible to all authenticated roles
- [ ] Excludes fully benched resources (0 assignments) and fully allocated resources (>= 100%)
- [ ] Unit tests for partial allocation scenarios

---

## Story: Add bench cost fields to bench API (Phase 2)
**Type:** Feature
**Phase:** 2
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (loaded cost, bench cost engine), 10-bench-forecasting (bench list API)
**Labels:** backend

### Description
Extend `GET /api/bench` and `GET /api/bench/summary` to populate the bench cost fields that were null in Phase 1. daily_bench_cost_inr = loaded_cost_monthly / working_days_per_month. total_bench_cost_inr = daily_cost * days_on_bench. Aggregate total_bench_cost_inr in summary. Cost fields restricted to CEO, CTO, Finance (return null for other roles).

### Acceptance Criteria
- [ ] daily_bench_cost_inr populated: loaded_cost_monthly / system.working_days_per_month
- [ ] total_bench_cost_inr populated: daily_cost * days_on_bench
- [ ] Returns null for resources without loaded_cost_monthly
- [ ] Summary endpoint returns aggregate total_bench_cost_inr
- [ ] Cost fields restricted to CEO, CTO, Finance (null for others)
- [ ] Uses SystemConfig for working_days_per_month (not hardcoded)
- [ ] Unit tests for cost calculations and access restriction

---

## Story: Implement early release tracking
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** 05-allocation-tracking, 13-audit-history
**Labels:** backend

### Description
When a resource is released before their planned end_date (released_at < end_date), flag this as an early release in the AuditLog. The early release flag should be visible in the resource's assignment history. This is a detection/logging concern -- no new API endpoints, but the audit log entry should include metadata indicating early release.

### Acceptance Criteria
- [ ] Early release detected when released_at < end_date on an assignment
- [ ] AuditLog entry includes early release indication (e.g., field_name = "early_release", new_value = "true")
- [ ] Visible in resource's assignment history via existing audit log queries
- [ ] No false positives: only flags when released_at is strictly before end_date
- [ ] Unit tests for early release detection

---

## Story: Build resource availability view UI
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 10-bench-forecasting (all Phase 1 APIs)
**Labels:** frontend

### Description
Build the `/availability` page with four tabbed sections: Bench, Partially Available, Releasing Soon, and Fully Allocated. Include resource name search, 30/60/90 day filter on Releasing Soon tab, and summary bar (bench count, bench cost total in Phase 2). All tabs visible to all authenticated roles including Engineer. Bench cost column visible only to CEO/CTO/Finance.

### Acceptance Criteria
- [ ] Four tabs: Bench / Partial / Releasing Soon / Fully Allocated
- [ ] Bench tab: Name (link to profile), Designation, Expertise, Days on Bench, Tags (pill badges)
- [ ] Bench tab Phase 2: Daily/Total Bench Cost columns visible to CEO/CTO/Finance only
- [ ] Partially Available tab: Name, Total Allocation %, Spare Capacity %, Current Projects
- [ ] Releasing Soon tab: Name, Project, Allocation %, Release Date, Days Remaining countdown
- [ ] Releasing Soon tab: 30/60/90 day filter toggle
- [ ] Fully Allocated tab: Name, Total Allocation %, Projects
- [ ] Search input filters by resource name across all tabs
- [ ] Summary bar: bench count; bench cost total (Phase 2, restricted)
- [ ] Click resource name navigates to resource profile (if role has access)
- [ ] Click project name navigates to project detail (if role has access)
- [ ] Per-section empty states
- [ ] Visible to all roles including Engineer
- [ ] Billing rates, billability %, CTC, shadow status NOT shown to Engineer or HR

---

## Story: Build bench summary dashboard widget
**Type:** Feature
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P2
**Estimate:** S (1-2d)
**Depends On:** 10-bench-forecasting (bench summary API), 07-utilization-dashboards
**Labels:** frontend

### Description
Add a bench summary widget to the company dashboard (`/dashboard`). Displays bench count (large number), expandable list of benched resource names with days on bench, total bench cost INR (Phase 2, restricted to CEO/CTO), and link to full availability view.

### Acceptance Criteria
- [ ] Bench count displayed as large number
- [ ] Expandable list of benched resources with days on bench
- [ ] Total bench cost INR shown in Phase 2 (CEO/CTO only)
- [ ] Link to `/availability` for full view
- [ ] Bench cost hidden from all roles except CEO and CTO
- [ ] Widget handles zero-bench-count state gracefully

---

## Story: Implement bench forecasting access control
**Type:** Task
**Phase:** 1
**Module:** 10-bench-forecasting
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles, 10-bench-forecasting (all APIs)
**Labels:** backend

### Description
Enforce access control per ACCESS-MATRIX.md for bench and availability data. All authenticated roles can view resource availability (bench_data: VIEW ALL for most roles). Financial data (bench cost) restricted to CEO, CTO, Finance. Engineer sees availability but not billing rates, billability, CTC, or shadow status. Ensure cost fields return null (not omitted) for unauthorized roles.

### Acceptance Criteria
- [ ] All authenticated roles can access GET /api/bench, /api/bench/summary, /api/availability/upcoming, /api/availability/partial
- [ ] Bench cost fields return null for roles without bench_data financial access
- [ ] Engineer sees resource names and availability but not financial or sensitive fields
- [ ] HR sees profiles and availability but not financial fields
- [ ] Response shape consistent (fields present but null when restricted)
- [ ] Access control tests for all 7 roles
