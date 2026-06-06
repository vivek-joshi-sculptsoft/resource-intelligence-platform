# Non-Human Costs — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Access control middleware, User entity | Cost entry endpoints must check RolePermission for the `non_human_costs` data type. PM, DM, CTO, CEO, and Finance can add/edit costs; HR and Engineer cannot. User entity is referenced by the `created_by` FK on each cost entry. |
| 03-project-management | Project entity (`id`, `name`, `client_id`, `type`, `status`) | Non-human cost line items are linked to projects via `project_id` FK. Project name and client are displayed in cost views. Costs are grouped and filtered by project. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 07-utilization-dashboards | NonHumanCost entity for Phase 2 financial widgets. Reads `project_id`, `amount_inr`, `is_recurring`, `cost_date`, `recurring_end_date` to compute non-human cost totals in project-level and company-level dashboards. |
| 08-financial-engine | NonHumanCost entity for Total Project Cost calculation. Non-human costs feed into: `Total Project Cost = Resource Cost + Non-Human Cost (INR)`. Reads `project_id`, `amount_inr`, `is_recurring`, `cost_date`, `recurring_end_date`. |
| 12-alerts | NonHumanCost entity indirectly. Recurring cost processing is a scheduled job (1st of each month) that auto-creates monthly entries for active recurring costs. |
| 13-audit-history | NonHumanCost entity tracked for audit logging. All fields are tracked for CREATE, UPDATE, and DELETE operations. |

## Shared References Used
- `shared/ENTITIES.md` — Defines the NonHumanCost entity (section 2.10) owned by this module. References Project (section 2.6) and User (section 2.3) from other modules.
- `shared/BUSINESS-RULES.md` — Section 7.7 (Exchange Rate Conversion) for the `amount_inr = amount x exchange_rate` formula. Section 7.2 (Project Cost) for how non-human costs feed into Total Project Cost: `Non-Human Cost (INR) = SUM(amount_inr for one-time in month) + SUM(amount_inr for active recurring)`.
- `shared/ACCESS-MATRIX.md` — Defines access rules for the `non_human_costs` data type: PM/DM/CTO/CEO have EDIT access; Finance has EDIT ALL; HR and Engineer have NONE.
