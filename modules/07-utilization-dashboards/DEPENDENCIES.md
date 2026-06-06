# Utilization Dashboards — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Access control middleware, Role entity | Dashboard data is filtered by role scope. CEO/CTO see company-wide metrics; DM/PM see their portfolio only. Financial widgets (Phase 2) are restricted to CEO/CTO/Finance. Engineers see only the resource availability view with non-sensitive fields. |
| 04-resource-management | Resource entity (`id`, `name`, `designation`, `technical_expertise`, `date_of_joining`, `is_active`, tags) | Used for bench detection (resources with 0 active assignments), availability calculations, and per-resource utilization metrics. Phase 2 adds `loaded_cost_monthly` for cost and bench cost calculations. |
| 03-project-management | Project entity (`id`, `name`, `client_id`, `type`, `status`, `dm_id`, `pm_id`, `billing_currency`, `contract_end_date`) | Used for project-level dashboard aggregations, DM-level portfolio filtering, and active project counts by type. |
| 05-allocation-tracking | Assignment entity (`resource_id`, `project_id`, `allocation_pct`, `billability_pct`, `is_shadow`, `status`, `start_date`, `end_date`, `released_at`) | Primary data source for all utilization and allocation calculations. Company utilization formula, bench detection, shadow allocation tracking, and upcoming release lists all derive from assignment data. |
| 02-client-management | Client entity (`id`, `name`, `is_active`) | Used for client-level dashboard aggregations. Client name displayed in client dashboard views. Active project and resource counts are grouped by client. |

### Phase 2 Additional Dependencies

| Module | What's Needed | Why |
|---|---|---|
| 08-financial-engine | Financial calculation endpoints (resource cost, projected revenue, actual revenue, margin) | Phase 2 financial widgets on dashboards require the financial engine's cost and revenue computations. Revenue summary (projected vs actual) and margin displays at project, client, and company levels. |
| 09-invoicing | Invoice entity (`project_id`, `amount_inr`, `status`, `invoice_date`) and Milestone entity (`project_id`, `planned_delivery_date`, `status`) | Phase 2 actual revenue data comes from invoices. Overdue milestone count in company dashboard reads milestones past their `planned_delivery_date`. |
| 06-non-human-costs | NonHumanCost entity (`project_id`, `amount_inr`, `is_recurring`, `cost_date`, `recurring_end_date`) | Phase 2 project-level and company-level cost dashboards include non-human cost totals alongside resource costs. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 08-financial-engine | Existing dashboard views. The financial engine adds financial widgets (cost, revenue, margin) to the dashboards already built by this module in Phase 1. This is an update to existing views, not a new dependency. |
| 12-alerts | Utilization data for the UTILIZATION_DROP alert. The weekly scheduled job checks whether company utilization falls below `alert.utilization_threshold_pct` (default 70%), using the same utilization calculation this module provides. |

## Shared References Used
- `shared/ENTITIES.md` — References Assignment (section 2.7), Resource (section 2.5), Project (section 2.6), Client (section 2.4), Invoice (section 2.9), Milestone (section 2.8), and NonHumanCost (section 2.10). This module owns no entities of its own.
- `shared/BUSINESS-RULES.md` — Section 7.1 (Resource Utilization) for company utilization formula. Section 7.2 (Project Cost) for Phase 2 cost widgets. Section 7.3 (Projected Revenue) for Phase 2 revenue widgets. Section 7.4 (Actual Revenue) for Phase 2 invoice-based revenue. Section 7.5 (Margin) for Phase 2 margin calculations. Section 7.6 (Bench Cost) for Phase 2 bench cost display. Section 7.7 (Exchange Rate Conversion) for multi-currency support in financial displays.
- `shared/ACCESS-MATRIX.md` — Defines access rules for `resource_availability` (VIEW ALL for all roles including Engineer), `bench_data` (financial data restricted to CEO/CTO/Finance), `project_margin` (CEO/CTO/Finance, DM configurable), `billability` (hidden from HR/Engineer), and `shadow_assignments` (hidden from HR/Engineer). Dashboard content varies by role.
