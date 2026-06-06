# Allocation Tracking — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Access control middleware, Role entity, User entity | Assignment endpoints must check RolePermission for `allocation`, `billability`, `billing_rates`, and `shadow_assignments` data types. PM has EDIT OWN_PORTFOLIO; DM has EDIT OWN_PORTFOLIO; Engineer has VIEW SELF_ONLY. Sensitive fields (`billing_rate`, `billability_pct`, `is_shadow`) are hidden from unauthorized roles. |
| 03-project-management | Project entity (`id`, `name`, `type`, `status`, `dm_id`, `pm_id`, `billing_currency`) | Assignments are linked to projects via `project_id` FK. Project must have `status = ACTIVE` to create new assignments. Project completion/cancellation triggers cascading auto-release of all active assignments. `billing_currency` determines the currency for `billing_rate` (Phase 2). |
| 04-resource-management | Resource entity (`id`, `name`, `designation`, `technical_expertise`, `is_active`) | Assignments are linked to resources via `resource_id` FK. Resource must be active to receive new assignments. Resource `designation` and `technical_expertise` provide fallback values for designation resolution. Resource deactivation triggers release of all active assignments. Phase 2 uses `loaded_cost_monthly` for cost calculations. |
| 13-audit-history | AuditLog entity and logging infrastructure | All assignment CREATE, UPDATE, and status changes must be audit logged from day one. One audit row per changed field. The auto-release daily job also writes audit rows for each released assignment. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 02-client-management | Assignment entity (read-only) to count distinct active resources deployed on a client's projects for the client dashboard. Reads `project_id`, `resource_id`, `status`. |
| 07-utilization-dashboards | Assignment entity as the primary data source for all utilization and allocation metrics. Reads `resource_id`, `project_id`, `allocation_pct`, `billability_pct`, `is_shadow`, `status`, `start_date`, `end_date`, `released_at`. Used for company utilization, bench detection, availability views, and per-resource/per-project breakdowns. |
| 08-financial-engine | Assignment entity with `billing_rate` (Phase 2). Used for projected revenue calculation (`billability_pct / 100 x working_days x 8 x billing_rate`) and resource cost calculation (`loaded_cost_monthly x allocation_pct / 100`). |
| 10-bench-forecasting | Assignment entity for determining bench status (resources with 0 active assignments), partial availability (total allocation < 100%), and upcoming releases (assignments with `end_date` in the next 30/60/90 days). |
| 11-worklog | Assignment entity to validate that an employee has an ACTIVE assignment on a project before allowing worklog entries. Reads `resource_id`, `project_id`, `status`, `start_date`, `end_date`. |
| 12-alerts | Assignment entity for over-allocation alerts (total allocation > 100%) and assignment auto-released alerts. The auto-release daily job (owned by this module) creates alert rows for PM and DM on each release. |

## Shared References Used
- `shared/ENTITIES.md` — Defines the Assignment entity (section 2.7) owned by this module. References Project (section 2.6), Resource (section 2.5), AuditLog (section 2.11), and Alert (section 2.12) from other modules.
- `shared/BUSINESS-RULES.md` — Section 7.1 (Resource Utilization) for total allocation and billable allocation formulas. Section 7.2 (Project Cost) for shadow cost inclusion. Section 7.3 (Projected Revenue) for billing rate calculation (Phase 2). Section 8 (Auto-Release) for the daily job algorithm and edge cases. Section 11 (Designation Resolution) for the fallback rule.
- `shared/ACCESS-MATRIX.md` — Defines access rules for `allocation`, `billability`, `billing_rates`, and `shadow_assignments` data types. Determines who can view/edit assignment fields and at what scope (ALL, OWN_PORTFOLIO, SELF_ONLY).
