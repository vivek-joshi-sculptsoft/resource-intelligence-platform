# Auth & Roles — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| _None_ | _This is the root module_ | Auth & Roles has no upstream dependencies. It is the foundation that all other modules depend on. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 02-client-management | Access control middleware to enforce role-based visibility and edit permissions on client data (`client_profiles` data type). |
| 03-project-management | Access control middleware for project CRUD; Role and User entities to resolve DM/PM scope filtering (`OWN_PORTFOLIO`). |
| 04-resource-management | Access control middleware for resource profiles; field-level restrictions to hide `loaded_cost_monthly` from non-financial roles. User entity to link login accounts to resource profiles via `User.resource_id`. |
| 05-allocation-tracking | Access control middleware for assignment CRUD; role-based field restrictions on `billing_rate`, `billability_pct`, and `is_shadow`. |
| 06-non-human-costs | Access control middleware; User entity for `created_by` field on cost entries. |
| 07-utilization-dashboards | Access control middleware to enforce role-based dashboard scoping (company-wide for CEO/CTO, portfolio-scoped for DM/PM); field-level restrictions to hide financial widgets from unauthorized roles. |
| 08-financial-engine | Access control middleware; field-level restrictions on `ctc_loaded_cost`, `billing_rates`, and `project_margin` data types. |
| 09-invoicing | Access control middleware; Finance role identification for invoice status transitions. |
| 10-bench-forecasting | Access control middleware; role-based restriction on bench cost data (CEO/CTO/Finance only). |
| 11-worklog | Access control middleware; User entity to identify the logged-in employee for `SELF_ONLY` scope on worklog entries. |
| 12-alerts | Access control middleware; Role entity for determining alert recipients by role; SystemConfig entity (seeded in this module) for alert threshold values. |
| 13-audit-history | Access control middleware for audit log viewer access (CEO/CTO only for full history; DM/PM for own portfolio). User entity for `changed_by` field on every audit row. |

## Shared References Used
- `shared/ENTITIES.md` — Defines Role (section 2.1), RolePermission (section 2.2), and User (section 2.3) entities owned by this module.
- `shared/BUSINESS-RULES.md` — Not directly used. This module does not perform calculations.
- `shared/ACCESS-MATRIX.md` — Defines the full 105-row RolePermission seed data (7 roles x 15 data types), scope rules, field-level restrictions, and the runtime access check algorithm that this module implements as middleware.
