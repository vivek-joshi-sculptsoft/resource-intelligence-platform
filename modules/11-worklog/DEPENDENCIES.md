# Worklog — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Role, RolePermission, User entities | Access control: Engineers create/edit own worklogs (SELF_ONLY scope). PM/DM view own portfolio worklogs (OWN_PORTFOLIO). CEO/CTO view all. RolePermission governs the `worklogs` data type. |
| 03-project-management | Project entity (`worklog_enabled`, `pm_id`, `dm_id`) | The `worklog_enabled` toggle determines whether employees can log hours against a project. PM/DM portfolio scoping uses `pm_id` and `dm_id` for worklog viewing access. |
| 04-resource-management | Resource entity (`id`, `name`) | Worklog entries reference `resource_id`. Resource name is displayed in manager worklog views. |
| 05-allocation-tracking | Assignment entity (`resource_id`, `project_id`, `status`) | Employees can only log hours against projects where they have an ACTIVE assignment. Backfill validation checks whether the resource had an ACTIVE assignment on the logged date. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 13-audit-history | Worklog create/update/delete operations are captured by the audit logging infrastructure. |

## Shared References Used
- `shared/ENTITIES.md` — Worklog (2.11) field definitions, decoupled-by-design note (no FK to Invoice, Assignment billability, or any financial entity); Assignment (2.7) for active assignment validation
- `shared/BUSINESS-RULES.md` — Not directly used. Worklog is deliberately decoupled from all financial calculations (billing, invoicing, revenue, margin).
- `shared/ACCESS-MATRIX.md` — `worklogs` data type: Engineer EDIT SELF_ONLY, PM/DM VIEW OWN_PORTFOLIO, CEO/CTO VIEW ALL, Finance NONE, HR NONE
