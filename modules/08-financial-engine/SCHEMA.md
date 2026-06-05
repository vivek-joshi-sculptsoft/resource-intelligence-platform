# Module 08: Financial Engine — Schema

## Entities Owned by This Module

**None.** This module activates fields on existing entities owned by other modules. No new tables are created.

---

## Fields Activated in Phase 2

### Resource.loaded_cost_monthly (owned by Module 04)

| Field | Type | Notes |
|---|---|---|
| loaded_cost_monthly | DECIMAL(15,2) NULLABLE | CTC + overhead per month in INR. Was null in Phase 1. Restricted to CEO/CTO/Finance. |

Migration: column already exists as NULLABLE from Phase 1 schema. No schema change required — just begin populating it.

See `shared/ENTITIES.md §2.5`.

### Assignment.billing_rate (owned by Module 05)

| Field | Type | Notes |
|---|---|---|
| billing_rate | DECIMAL(10,2) NULLABLE | Per-hour rate in project's billing_currency. Was null in Phase 1. Null for shadow assignments. |

Migration: column already exists as NULLABLE from Phase 1 schema. No schema change required — just begin populating it.

See `shared/ENTITIES.md §2.7`.

---

## Entities Referenced from Other Modules

### Resource (Module 04)
`id`, `name`, `loaded_cost_monthly`, `is_active`

### Assignment (Module 05)
`project_id`, `resource_id`, `allocation_pct`, `billability_pct`, `is_shadow`, `billing_rate`, `status`, `start_date`, `end_date`, `released_at`

### Project (Module 03)
`id`, `name`, `client_id`, `billing_currency`, `status`

### Invoice (Module 09)
`project_id`, `amount_inr`, `status` (APPROVED or PAID only for actual revenue)

### NonHumanCost (Module 06)
`project_id`, `amount_inr`, `is_recurring`, `cost_date`, `recurring_end_date`

### SystemConfig (Module 12)
`system.working_days_per_month` (default 22), `system.working_hours_per_day` (default 8)
