# Project Management — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Access control middleware, Role entity, User entity | Every project endpoint must check RolePermission. DM and PM use `OWN_PORTFOLIO` scope filtering (`dm_id` / `pm_id = current user`). |
| 02-client-management | Client entity (`id`, `name`, `is_active`) | Every project has a required `client_id` FK. Client name is displayed in project lists and detail views. Cannot create projects under inactive clients. |
| 04-resource-management | Resource entity (`id`, `name`, `designation`) | Project requires `dm_id` and `pm_id` (both FK to Resource). Resource names are displayed for DM/PM fields. Only active resources can be assigned as DM or PM. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 05-allocation-tracking | Project entity (`id`, `status`, `dm_id`, `pm_id`, `billing_currency`, `type`). Assignments are created against projects. Project status must be ACTIVE to create assignments. Project completion/cancellation triggers auto-release of all active assignments. |
| 06-non-human-costs | Project entity (`id`, `name`, `client_id`, `type`, `status`). Non-human cost line items are linked to projects via `project_id` FK. |
| 07-utilization-dashboards | Project entity for project-level and DM-level dashboard aggregations. Reads `dm_id`, `pm_id`, `status`, `type`, `client_id`, `contract_end_date` for filtering and grouping. |
| 08-financial-engine | Project entity for project-level financial calculations (cost, revenue, margin). Uses `billing_currency` and `contract_value` (Phase 2, FP only). |
| 09-invoicing | Project entity (`id`, `type`, `billing_currency`). Invoices are linked to projects. Milestones are only created for FIXED_PRICE projects. Invoice currency is copied from project `billing_currency`. |
| 10-bench-forecasting | Project entity indirectly via Assignment. Project names shown alongside upcoming resource releases. |
| 11-worklog | Project entity (`id`, `worklog_enabled`, `pm_id`, `dm_id`). Employees can only log hours on projects where `worklog_enabled = true`. Manager worklog viewing is scoped by `pm_id` / `dm_id`. |
| 12-alerts | Project entity for contract expiry alerts (`contract_end_date`), milestone overdue alerts (via milestones linked to projects), and over-allocation alerts (via assignments linked to projects). |
| 13-audit-history | Project entity tracked for audit logging. Tracked fields: `status`, `contract_end_date`, `contract_value`. |

## Shared References Used
- `shared/ENTITIES.md` — Defines the Project entity (section 2.6) owned by this module. References Client (section 2.4), Resource (section 2.5), and Assignment (section 2.7) from other modules.
- `shared/BUSINESS-RULES.md` — Section 7.2 (Project Cost) and 7.3 (Projected Revenue) reference project-level data in Phase 2. Status machine transitions defined in FSD section 6.4.
- `shared/ACCESS-MATRIX.md` — Defines access rules for the `project_details` data type: CEO/CTO have EDIT ALL; DM/PM have EDIT OWN_PORTFOLIO; Finance has VIEW ALL; HR has VIEW ALL; Engineer has VIEW SELF_ONLY.
