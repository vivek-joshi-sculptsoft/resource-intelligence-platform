# Module 08: Financial Engine

## Overview

The Financial Engine activates the money layer. It introduces `loaded_cost_monthly` on Resource and `billing_rate` on Assignment, then wires up all the financial calculations: resource cost, projected revenue, actual revenue, and margin — at project, client, and company levels. This module adds no new entities; it activates fields and calculation endpoints on existing data. All formulas are in `shared/BUSINESS-RULES.md`.

## Phase

Phase 2.

## Dependencies

- Module 01 (Auth & Roles)
- Module 04 (Resource Management) — adds `loaded_cost_monthly` field
- Module 05 (Allocation Tracking) — adds `billing_rate` field
- Module 06 (Non-Human Costs) — non-human costs feed into Total Project Cost
- Module 07 (Utilization Dashboards) — financial widgets added to existing dashboards
- Module 09 (Invoicing) — actual revenue comes from invoice amounts

---

## Features

### Feature: Resource Loaded Cost Entry
**Description:** Enter or update a resource's loaded cost (CTC + overhead per month in INR).
**Acceptance Criteria:**
- [ ] CEO, CTO, Finance can set `loaded_cost_monthly` on any resource
- [ ] Field is null in Phase 1; must be activated in Phase 2 migration
- [ ] Changes audit logged with old/new values
- [ ] Field is hidden from all other roles (`null` in API response)

### Feature: Billing Rate per Assignment
**Description:** Set per-resource per-project billing rate in project billing currency.
**Acceptance Criteria:**
- [ ] PM, DM, CEO, CTO can set `billing_rate` on an assignment
- [ ] Rate is in the project's `billing_currency`
- [ ] Shadow assignments: `billing_rate` must be null (no billing for shadow)
- [ ] Field is restricted per `shared/ACCESS-MATRIX.md` (`billing_rates`)

### Feature: Resource Cost Calculation per Project
**Description:** Monthly resource cost for a project based on loaded costs and allocations.
**Acceptance Criteria:**
- [ ] Computed: `SUM(resource.loaded_cost_monthly × assignment.allocation_pct / 100)` for all ACTIVE assignments
- [ ] Shadow resources are included in cost
- [ ] Returns null if any resource lacks `loaded_cost_monthly`

### Feature: Projected Revenue Calculation
**Description:** Calculate expected revenue from billability and billing rates.
**Acceptance Criteria:**
- [ ] Per assignment: `billability_pct / 100 × working_days × 8 × billing_rate`
- [ ] Summed for all non-shadow ACTIVE assignments
- [ ] Converted to INR using latest exchange rate (or 1.0 for INR projects)
- [ ] Returns null if any assignment lacks `billing_rate`

### Feature: Actual Revenue from Invoices
**Description:** Sum of paid/approved invoice amounts.
**Acceptance Criteria:**
- [ ] `SUM(invoice.amount_inr)` where status ∈ {APPROVED, PAID}
- [ ] Per project, per client, company-wide aggregations all supported

### Feature: Margin Calculations
**Description:** Both projected and actual margin at project, client, and company level.
**Acceptance Criteria:**
- [ ] Projected Margin = Projected Revenue (INR) − Total Project Cost
- [ ] Actual Margin = Actual Revenue (INR) − Total Project Cost
- [ ] Margin % = Margin / Revenue × 100
- [ ] Null-safe: if cost or revenue is null, margin is null
- [ ] Restricted: only CEO, CTO, Finance, and DM (configurable) see margin fields

### Feature: Bench Cost Calculation
**Description:** Cost of resources sitting on bench.
**Acceptance Criteria:**
- [ ] Daily bench cost = `loaded_cost_monthly / 22`
- [ ] Total bench cost = `daily_cost × days_on_bench`
- [ ] Bench start = max(released_at) of last assignment, or date_of_joining if never assigned
- [ ] Restricted: CEO, CTO, Finance only

---

## Validations

No new entity validations. Field-level:
- `loaded_cost_monthly` must be > 0 if provided (null is allowed — means not yet entered)
- `billing_rate` must be > 0 if provided

---

## Business Rules

All from `shared/BUSINESS-RULES.md`:
- §7.2 Project Cost
- §7.3 Projected Revenue
- §7.4 Actual Revenue
- §7.5 Margin
- §7.6 Bench Cost
- §7.7 Exchange Rate Conversion

Access restrictions for financial data: `shared/ACCESS-MATRIX.md` — `ctc_loaded_cost`, `billing_rates`, `project_margin`
