# Module 08: Financial Engine -- JIRA Tickets

---

## Story: Add loaded_cost_monthly and billing_rate activation migration
**Type:** Task
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 04-resource-management, 05-allocation-tracking
**Labels:** backend, database

### Description
Create a Phase 2 database migration that confirms the `loaded_cost_monthly` column on Resource and the `billing_rate` column on Assignment exist as NULLABLE (they were defined in Phase 1 but left unused). Add any missing indexes. No schema changes are expected -- this is a verification and documentation migration. Ensure SystemConfig keys `system.working_days_per_month` and `system.working_hours_per_day` are seeded if not already present.

### Acceptance Criteria
- [ ] Migration verifies `Resource.loaded_cost_monthly` (DECIMAL(15,2) NULLABLE) exists
- [ ] Migration verifies `Assignment.billing_rate` (DECIMAL(10,2) NULLABLE) exists
- [ ] SystemConfig entries `system.working_days_per_month` (22) and `system.working_hours_per_day` (8) are seeded
- [ ] Migration is idempotent and safe to re-run

---

## Story: Build resource loaded cost entry API
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 04-resource-management, 01-auth-and-roles, 13-audit-history (logging wrapper)
**Labels:** backend

### Description
Enable CEO, CTO, and Finance roles to set and update `loaded_cost_monthly` on a Resource via the existing `PUT /api/resources/:id` endpoint (Module 04). The field must be hidden (returned as `null`) for all other roles. Validate that the value is > 0 when provided. All changes must be audit logged with old/new values.

### Acceptance Criteria
- [ ] CEO, CTO, Finance can set `loaded_cost_monthly` on any resource via PUT
- [ ] Value must be > 0 when provided; null is allowed (means not yet entered)
- [ ] API response returns `loaded_cost_monthly: null` for DM, PM, HR, Engineer roles
- [ ] Changes are audit logged with field name, old value, new value
- [ ] Returns 403 if unauthorized role attempts to write the field
- [ ] Unit tests for happy path and access control

---

## Story: Build billing rate per assignment API
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 05-allocation-tracking, 03-project-management, 01-auth-and-roles
**Labels:** backend

### Description
Enable PM, DM, CEO, and CTO to set `billing_rate` on an Assignment. The rate is denominated in the project's `billing_currency`. Shadow assignments must always have `billing_rate = null`. Field visibility is governed by the `billing_rates` data type in `shared/ACCESS-MATRIX.md`. All changes must be audit logged.

### Acceptance Criteria
- [ ] PM, DM, CEO, CTO can set `billing_rate` on an assignment via PUT
- [ ] `billing_rate` must be > 0 when provided
- [ ] Shadow assignments: `billing_rate` must be null; reject attempts to set a rate on shadow
- [ ] Field is returned as `null` to roles without `billing_rates` VIEW access (per ACCESS-MATRIX)
- [ ] Changes are audit logged
- [ ] Unit tests for shadow enforcement, access control, and validation

---

## Story: Build resource cost calculation engine
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (loaded cost entry), 06-non-human-costs
**Labels:** backend

### Description
Implement the resource cost calculation per project according to BUSINESS-RULES.md Section 7.2. Resource Cost = `SUM(loaded_cost_monthly * allocation_pct / 100)` for all ACTIVE assignments. Shadow resources are included in cost. Non-human costs are summed from Module 06. Total Project Cost = Resource Cost + Non-Human Cost. Returns null if any contributing resource lacks `loaded_cost_monthly`, with a `missing_costs` list identifying those resources.

### Acceptance Criteria
- [ ] Resource Cost computed as SUM(loaded_cost_monthly * allocation_pct / 100) for ACTIVE assignments
- [ ] Shadow resources are included in cost calculation
- [ ] Non-Human Cost summed from NonHumanCost entity (amount_inr for the project)
- [ ] Total Project Cost = Resource Cost + Non-Human Cost
- [ ] Returns null for cost if any resource lacks `loaded_cost_monthly`
- [ ] Returns `missing_costs` array listing resource names with null loaded cost
- [ ] Uses `system.working_days_per_month` from SystemConfig (not hardcoded 22)
- [ ] Unit tests with known input/output values matching BUSINESS-RULES.md Section 7.2

---

## Story: Build projected revenue calculation engine
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (billing rate API)
**Labels:** backend

### Description
Implement projected revenue calculation per BUSINESS-RULES.md Section 7.3. Per assignment: `billability_pct / 100 * working_days * working_hours * billing_rate`. Sum across all non-shadow ACTIVE assignments. Convert to INR using the project's exchange rate (1.0 for INR). Returns null and a `missing_rates` list if any assignment lacks `billing_rate`.

### Acceptance Criteria
- [ ] Per-assignment projected revenue = `billability_pct / 100 * working_days * 8 * billing_rate`
- [ ] Summed for all non-shadow ACTIVE assignments on the project
- [ ] Shadow assignments excluded from projected revenue
- [ ] Converted to INR using latest exchange rate (1.0 for INR projects)
- [ ] Returns null if any non-shadow assignment lacks `billing_rate`
- [ ] Returns `missing_rates` array listing resources with null billing rate
- [ ] Uses SystemConfig for working_days and working_hours (not hardcoded)
- [ ] Unit tests with known input/output values matching BUSINESS-RULES.md Section 7.3

---

## Story: Build actual revenue calculation from invoices
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 09-invoicing
**Labels:** backend

### Description
Implement actual revenue calculation per BUSINESS-RULES.md Section 7.4. Actual Revenue = `SUM(invoice.amount_inr)` where status is APPROVED or PAID. Support per-project, per-client, and company-wide aggregations.

### Acceptance Criteria
- [ ] Actual Revenue = SUM(invoice.amount_inr) where status in {APPROVED, PAID}
- [ ] Per-project aggregation supported
- [ ] Per-client aggregation supported (sum across client's projects)
- [ ] Company-wide aggregation supported (sum across all projects)
- [ ] Excludes DRAFT and SUBMITTED invoices
- [ ] Unit tests with known input/output values matching BUSINESS-RULES.md Section 7.4

---

## Story: Build margin calculation engine
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (resource cost, projected revenue, actual revenue)
**Labels:** backend

### Description
Implement margin calculations per BUSINESS-RULES.md Section 7.5. Projected Margin = Projected Revenue (INR) - Total Project Cost. Actual Margin = Actual Revenue (INR) - Total Project Cost. Margin % = Margin / Revenue * 100. All calculations are null-safe: if cost or revenue is null, margin is null. Support project, client, and company-level aggregation.

### Acceptance Criteria
- [ ] Projected Margin = Projected Revenue (INR) - Total Project Cost
- [ ] Actual Margin = Actual Revenue (INR) - Total Project Cost
- [ ] Margin % = Margin / Revenue * 100
- [ ] Null-safe: if cost or revenue is null, margin is null (not zero)
- [ ] Project-level margins computed
- [ ] Client-level margins = sum across client's projects
- [ ] Company-level margins = sum across all projects
- [ ] Restricted to CEO, CTO, Finance, and DM (configurable) per ACCESS-MATRIX
- [ ] Unit tests with known input/output values matching BUSINESS-RULES.md Section 7.5

---

## Story: Build multi-currency exchange rate conversion
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** none
**Labels:** backend

### Description
Implement the exchange rate conversion utility per BUSINESS-RULES.md Section 7.7. `amount_inr = amount * exchange_rate`. Exchange rate is manually entered (never auto-fetched). Auto-set to 1.0 for INR. This utility is used across financial calculations and invoice processing.

### Acceptance Criteria
- [ ] Conversion formula: `amount_inr = amount * exchange_rate`
- [ ] Exchange rate = 1 unit of billing currency = X INR
- [ ] Auto-set to 1.0 for INR currency
- [ ] Never auto-fetches rates from external APIs
- [ ] Shared utility available to financial engine and invoicing modules
- [ ] Unit tests for INR (rate=1.0), USD, EUR conversions

---

## Story: Build bench cost calculation engine
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (loaded cost entry), 05-allocation-tracking
**Labels:** backend

### Description
Implement bench cost calculations per BUSINESS-RULES.md Section 7.6. Daily bench cost = `loaded_cost_monthly / 22`. Total bench cost = `daily_cost * days_on_bench`. Bench start = max(released_at) of last assignment, or date_of_joining if never assigned. Per-resource and aggregate bench cost. Restricted to CEO, CTO, Finance.

### Acceptance Criteria
- [ ] Daily bench cost = `loaded_cost_monthly / system.working_days_per_month`
- [ ] Total bench cost = daily_cost * days_on_bench
- [ ] Bench start = max(released_at) of last assignment, or date_of_joining if never assigned
- [ ] Bench = resource with 0 ACTIVE assignments
- [ ] Returns null if resource has no loaded_cost_monthly
- [ ] Per-resource bench cost endpoint: GET /api/resources/:resourceId/bench-cost
- [ ] Restricted to CEO, CTO, Finance only
- [ ] Unit tests with known input/output values matching BUSINESS-RULES.md Section 7.6

---

## Story: Build project financials API endpoint
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (all calculation engines)
**Labels:** backend

### Description
Implement `GET /api/projects/:projectId/financials` that returns the full financial breakdown for a project: resource cost, non-human cost, total cost, projected revenue, actual revenue, projected/actual margins, resource cost breakdown, and missing data warnings. Access restricted per ACCESS-MATRIX: CEO/CTO/Finance (VIEW ALL), DM (OWN_PORTFOLIO, configurable for margin).

### Acceptance Criteria
- [ ] Returns resource_cost_inr, non_human_cost_inr, total_cost_inr
- [ ] Returns projected_revenue_inr, actual_revenue_inr
- [ ] Returns projected_margin_inr, projected_margin_pct, actual_margin_inr, actual_margin_pct
- [ ] Returns resource_cost_breakdown array with per-resource details
- [ ] Returns missing_costs and missing_rates arrays for incomplete data
- [ ] CEO, CTO, Finance see all fields
- [ ] DM sees only OWN_PORTFOLIO projects; margin visibility is configurable
- [ ] PM, HR, Engineer get 403
- [ ] Margin fields returned as null for roles without project_margin access
- [ ] Unit and integration tests for each role

---

## Story: Build client financials API endpoint
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 08-financial-engine (project financials API)
**Labels:** backend

### Description
Implement `GET /api/clients/:clientId/financials` that aggregates financial data across all of a client's projects. Returns totals for resource cost, non-human cost, projected/actual revenue, and margins, plus a per-project breakdown. Access restricted per ACCESS-MATRIX.

### Acceptance Criteria
- [ ] Aggregates financial data across all projects for the given client
- [ ] Returns per_project array with project-level summaries
- [ ] CEO, CTO, Finance see all fields
- [ ] DM sees only OWN_PORTFOLIO client data; margin configurable
- [ ] PM, HR, Engineer get 403
- [ ] Unit tests for aggregation logic and access control

---

## Story: Build company-wide financial dashboard API endpoint
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (project financials, bench cost)
**Labels:** backend

### Description
Implement `GET /api/dashboard/financials` that returns company-wide financial summary: total resource cost, total non-human cost, total cost, projected/actual revenue, projected/actual margin, bench cost with per-resource breakdown. Restricted to CEO, CTO, Finance only.

### Acceptance Criteria
- [ ] Returns total_resource_cost_inr, total_non_human_cost_inr, total_cost_inr
- [ ] Returns total_projected_revenue_inr, total_actual_revenue_inr
- [ ] Returns total_projected_margin_inr, total_actual_margin_inr
- [ ] Returns bench_cost_inr with bench_cost_breakdown per resource
- [ ] Restricted to CEO, CTO, Finance only
- [ ] All other roles get 403
- [ ] Unit tests for aggregation and access control

---

## Story: Build project financials tab UI
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 08-financial-engine (project financials API), 03-project-management (project detail page)
**Labels:** frontend

### Description
Add a "Financials" tab to the project detail view (`/projects/:id`). Display summary metrics row (Total Cost, Projected Revenue, Projected Margin %, Actual Revenue, Actual Margin %), a resource cost breakdown table, non-human cost total, and missing data warnings. Tab is visible only to CEO, CTO, Finance, and DM (with configurable margin access). All monetary values display in INR.

### Acceptance Criteria
- [ ] Financials tab added to project detail view
- [ ] Summary row displays: Total Cost, Projected Revenue, Projected Margin %, Actual Revenue, Actual Margin %
- [ ] Resource Cost Breakdown table shows: Resource name, Allocation %, Loaded Cost/Mo, Cost Contribution
- [ ] Non-Human Cost total displayed with link to costs tab
- [ ] Missing data warnings: "X resources are missing loaded cost" with link to resource profiles
- [ ] Tab only visible to CEO, CTO, Finance, DM
- [ ] Margin fields hidden for roles without project_margin access
- [ ] All monetary values displayed in INR format
- [ ] Empty state: "Financial data is not yet available..."
- [ ] Loading and error states handled

---

## Story: Add loaded cost field to resource profile UI
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 04-resource-management (resource profile page), 08-financial-engine (loaded cost API)
**Labels:** frontend

### Description
Add the `loaded_cost_monthly` field to the resource profile view. The field should be displayed and editable inline only for CEO, CTO, and Finance roles. Hidden entirely from all other roles.

### Acceptance Criteria
- [ ] "Loaded Cost (Monthly INR)" field displayed in resource profile for CEO/CTO/Finance
- [ ] Field is editable inline or via edit form
- [ ] Field is completely hidden from DM, PM, HR, Engineer
- [ ] Validates value > 0 on the client side
- [ ] Shows null/empty state when not yet entered

---

## Story: Add financial widgets to company dashboard
**Type:** Feature
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P2
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (company financials API), 07-utilization-dashboards
**Labels:** frontend

### Description
Add Phase 2 financial widgets to the company dashboard (`/dashboard`): Revenue Summary (Projected vs Actual bar comparison), Total Company Cost, Company Margin, and Bench Cost widgets. All restricted to CEO and CTO.

### Acceptance Criteria
- [ ] Revenue Summary widget: Projected Revenue vs Actual Revenue (INR bar/comparison)
- [ ] Total Company Cost widget
- [ ] Company Margin widget (projected and actual)
- [ ] Bench Cost widget with total and expandable breakdown
- [ ] All widgets restricted to CEO and CTO only
- [ ] Widgets hidden from all other roles
- [ ] Widgets handle null/incomplete data gracefully

---

## Story: Implement financial data access control and field restrictions
**Type:** Task
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 01-auth-and-roles, 08-financial-engine (all APIs)
**Labels:** backend

### Description
Enforce field-level and scope-level access control across all financial endpoints per ACCESS-MATRIX.md. Sensitive fields (loaded_cost_monthly, billing_rate, margins) must return `null` for unauthorized roles -- not omit the field. DM margin access is configurable via `is_configurable = true` on the `project_margin` and `billing_rates` RolePermission rows. Scope filtering (ALL, OWN_PORTFOLIO) must be applied as WHERE clauses at the database level.

### Acceptance Criteria
- [ ] loaded_cost_monthly returns null for DM, PM, HR, Engineer
- [ ] billing_rate returns null for PM, HR, Engineer; DM access is configurable
- [ ] All margin fields return null for unauthorized roles
- [ ] DM configurable access for project_margin and billing_rates works via RolePermission
- [ ] Scope filtering applied at database query level (WHERE clause), not post-fetch
- [ ] Response shape is consistent regardless of role (fields present but null)
- [ ] Access control tests for all 7 roles on each financial endpoint

---

## Story: Write validation and formula tests for financial engine
**Type:** Task
**Phase:** 2
**Module:** 08-financial-engine
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 08-financial-engine (all calculation engines)
**Labels:** backend

### Description
Comprehensive test suite covering all financial formulas from BUSINESS-RULES.md Sections 7.2-7.7. Each formula must have tests with known input/output values. Edge cases: null loaded costs, null billing rates, mixed currencies, shadow assignments, zero allocations, and single-resource projects.

### Acceptance Criteria
- [ ] Resource Cost (Section 7.2): tests with multiple resources, shadow inclusion, null cost handling
- [ ] Projected Revenue (Section 7.3): tests with billability percentages, shadow exclusion, null rate handling
- [ ] Actual Revenue (Section 7.4): tests filtering by APPROVED/PAID status only
- [ ] Margin (Section 7.5): tests for projected and actual, null-safety, percentage calculation
- [ ] Bench Cost (Section 7.6): tests for daily/total calculation, bench start logic
- [ ] Exchange Rate (Section 7.7): tests for INR auto-rate, multi-currency conversion
- [ ] Edge cases: empty project (no assignments), all nulls, single assignment
