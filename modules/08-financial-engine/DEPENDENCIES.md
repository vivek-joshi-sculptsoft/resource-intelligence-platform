# Financial Engine — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Role, RolePermission, User entities | Access control enforcement: only CEO, CTO, Finance can view loaded costs and margins. RolePermission governs field-level visibility for `ctc_loaded_cost`, `billing_rates`, and `project_margin` data types. |
| 02-client-management | Client entity | Client-level margin and revenue aggregations require `client_id` from Client records. |
| 03-project-management | Project entity (`billing_currency`, `status`, `client_id`) | Projected revenue uses `billing_currency` for rate context. Project cost and margin are computed per project. Project status filters (ACTIVE only) apply to all calculations. |
| 04-resource-management | Resource entity (`loaded_cost_monthly`) | Resource cost calculation uses `loaded_cost_monthly` field (activated in Phase 2). Bench cost uses this field divided by working days. Field already exists as NULLABLE from Phase 1 schema. |
| 05-allocation-tracking | Assignment entity (`allocation_pct`, `billability_pct`, `is_shadow`, `billing_rate`, `status`) | Resource cost = `loaded_cost_monthly x allocation_pct / 100`. Projected revenue = `billability_pct / 100 x working_days x 8 x billing_rate`. Shadow assignments contribute to cost but not revenue. `billing_rate` field activated in Phase 2. |
| 06-non-human-costs | NonHumanCost entity (`amount_inr`, `is_recurring`, `cost_date`) | Total Project Cost = Resource Cost + Non-Human Cost. Both one-time and recurring non-human costs feed into margin calculations. |
| 09-invoicing | Invoice entity (`amount_inr`, `status`) | Actual Revenue = `SUM(invoice.amount_inr)` where status is APPROVED or PAID. Actual Margin depends on invoice data. |
| 12-alerts | SystemConfig entity (`system.working_days_per_month`, `system.working_hours_per_day`) | Projected revenue formula uses working days (default 22) and working hours per day (default 8) from SystemConfig. Bench cost daily rate divides loaded cost by working days per month. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 07-utilization-dashboards | Phase 2 update adds financial widgets (margin, revenue, cost breakdowns) to existing dashboards. Uses all calculation endpoints from this module. |
| 10-bench-forecasting | Bench cost calculations require `loaded_cost_monthly` (activated by this module) and the bench cost formula from BUSINESS-RULES.md. |
| 12-alerts | UTILIZATION_DROP alert uses company utilization calculations. Financial thresholds may reference cost/margin data. |

## Shared References Used
- `shared/ENTITIES.md` — Resource (loaded_cost_monthly), Assignment (billing_rate), Project (billing_currency), Invoice (amount_inr), NonHumanCost (amount_inr), SystemConfig (working days/hours)
- `shared/BUSINESS-RULES.md` — All financial formulas: Resource Cost (7.2), Projected Revenue (7.3), Actual Revenue (7.4), Margin (7.5), Bench Cost (7.6), Exchange Rate Conversion (7.7)
- `shared/ACCESS-MATRIX.md` — Field-level restrictions for `ctc_loaded_cost`, `billing_rates`, `project_margin`; role-based visibility rules for financial data
