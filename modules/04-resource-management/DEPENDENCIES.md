# Resource Management — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Access control middleware, Role entity, User entity | Every resource endpoint must check RolePermission. HR has EDIT on `resource_profiles`; Engineer has VIEW SELF_ONLY. Field-level restriction hides `loaded_cost_monthly` from non-financial roles (returns `null`). User entity links login accounts to resources via `User.resource_id`. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 03-project-management | Resource entity (`id`, `name`, `designation`) for `dm_id` and `pm_id` FK fields on Project. Resource names displayed as Delivery Manager and Project Manager. |
| 05-allocation-tracking | Resource entity (`id`, `name`, `designation`, `technical_expertise`, `is_active`). Assignments link to resources via `resource_id` FK. Resource `designation` and `technical_expertise` serve as fallback values when `project_designation` / `project_expertise` are not set. Resource deactivation triggers release of all active assignments. Phase 2 adds `loaded_cost_monthly` for cost calculations. |
| 07-utilization-dashboards | Resource entity for bench detection, availability views, and per-resource utilization. Reads `id`, `name`, `designation`, `technical_expertise`, `date_of_joining`, `is_active`, and tags. Phase 2 adds `loaded_cost_monthly` for bench cost and revenue calculations. |
| 08-financial-engine | Resource entity's `loaded_cost_monthly` field (activated in Phase 2). Used in resource cost calculation: `loaded_cost_monthly x allocation_pct / 100` per active assignment. Also used for bench cost: `loaded_cost_monthly / 22` for daily bench cost. |
| 10-bench-forecasting | Resource entity for bench detection (resources with 0 active assignments). Reads `name`, `designation`, `technical_expertise`, `date_of_joining`, `is_active`, and tags. Phase 2 uses `loaded_cost_monthly` for bench cost calculations. |
| 11-worklog | Resource entity for linking worklog entries to the employee. Resource `id` used to validate active assignment before allowing worklog entry. |
| 12-alerts | Resource entity for bench duration alerts (resources on bench > threshold days). Also used for over-allocation alerts (total allocation across resource's assignments). |
| 13-audit-history | Resource entity tracked for audit logging. Tracked fields: `designation`, `loaded_cost_monthly`, `is_active`. |

## Shared References Used
- `shared/ENTITIES.md` — Defines the Resource entity (section 2.5) and ResourceTag join table owned by this module. References Assignment (section 2.7), Project (section 2.6), and User (section 2.3) from other modules for the resource profile view.
- `shared/BUSINESS-RULES.md` — Section 7.1 (Resource Utilization) for total allocation and billable allocation formulas. Section 7.6 (Bench Cost) for bench start computation and daily cost formula (Phase 2). Section 11 (Designation Resolution) for the fallback rule: `project_designation` if set, else `resource.designation`.
- `shared/ACCESS-MATRIX.md` — Defines access rules for `resource_profiles`, `ctc_loaded_cost`, and `resource_availability` data types. HR has EDIT on profiles but no access to financial fields. Engineer has VIEW SELF_ONLY on profiles and VIEW ALL on `resource_availability`.
