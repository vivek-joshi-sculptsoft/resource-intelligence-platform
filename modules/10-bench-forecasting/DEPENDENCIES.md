# Bench & Availability Forecasting — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Role, RolePermission, User entities | Access control: resource availability is visible to ALL roles including Engineer. Bench cost data (financial) is restricted to CEO, CTO, Finance via `bench_data` data type in RolePermission. |
| 03-project-management | Project entity (`name`, `client_id`) | Project names are displayed alongside upcoming availability data to show which projects resources are being released from. |
| 04-resource-management | Resource entity (`name`, `designation`, `technical_expertise`, `date_of_joining`, `loaded_cost_monthly`, `is_active`, tags) | Resource profiles are displayed on bench and availability lists. `date_of_joining` is the bench start date for resources never assigned. `loaded_cost_monthly` is needed for Phase 2 bench cost calculations. |
| 05-allocation-tracking | Assignment entity (`resource_id`, `project_id`, `allocation_pct`, `status`, `end_date`, `released_at`) | Core data source: bench = 0 ACTIVE assignments. Upcoming availability = ACTIVE assignments with `end_date` within the 30/60/90-day window. Partial availability = total `allocation_pct` < 100%. `released_at` determines bench start date. |
| 08-financial-engine | Bench cost formulas and `loaded_cost_monthly` activation | Phase 2 bench cost = `loaded_cost_monthly / 22 x days_on_bench`. The financial engine activates the loaded cost field and provides the calculation logic. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 07-utilization-dashboards | Phase 2 update may incorporate bench metrics and availability forecasts into dashboard views. |
| 12-alerts | BENCH_DURATION alert fires when a resource is on bench longer than `alert.bench_threshold_days`. Uses bench start date computation from this module's logic. |

## Shared References Used
- `shared/ENTITIES.md` — Resource (2.5) for profile fields and `loaded_cost_monthly`; Assignment (2.7) for allocation, status, end_date, and released_at; ResourceTag for tags display
- `shared/BUSINESS-RULES.md` — Bench Cost (7.6) formulas: daily bench cost, total bench cost, bench start date computation (max of released_at or date_of_joining)
- `shared/ACCESS-MATRIX.md` — `bench_data` data type: CEO/CTO/Finance/HR have VIEW ALL, PM has NONE, Engineer has VIEW ALL (availability only, no financial data); `resource_availability` visible to all roles
