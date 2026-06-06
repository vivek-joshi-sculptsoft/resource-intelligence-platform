# Audit History — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Role, RolePermission, User entities | `changed_by` field references the User entity. Access control for the Phase 3 viewer UI: CEO/CTO see full history, DM/PM see own portfolio entities only. User authentication is required to attribute every change. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 02-client-management | Audit logging wrapper for Client entity create/update/deactivate operations. |
| 03-project-management | Audit logging for Project entity. Tracked fields: status, contract_end_date, contract_value. |
| 04-resource-management | Audit logging for Resource entity. Tracked fields: designation, loaded_cost_monthly, is_active. |
| 05-allocation-tracking | Audit logging for Assignment entity. Tracked fields: ALL (allocation_pct, billability_pct, is_shadow, billing_rate, project_designation, project_expertise, start_date, end_date, status). Auto-release job writes audit entries. |
| 06-non-human-costs | Audit logging for NonHumanCost entity. Tracked fields: ALL fields. |
| 08-financial-engine | Audit logging for loaded_cost_monthly and billing_rate field changes on Resource and Assignment entities. |
| 09-invoicing | Audit logging for Milestone entity (status, planned_delivery_date, actual_delivery_date, amount) and Invoice entity (amount, exchange_rate, status). All lifecycle transitions are logged. |
| 11-worklog | Audit logging for Worklog create/update/delete operations. |
| 12-alerts | Audit logging for SystemConfig changes. Alert-triggered operations (e.g., auto-release) generate audit entries. |

## Shared References Used
- `shared/ENTITIES.md` — AuditLog (2.12) entity definition: immutable append-only table with entity_type, entity_id, action, field_name, old_value, new_value, changed_by, changed_at. BIGINT auto-increment PK (not UUID).
- `shared/BUSINESS-RULES.md` — Not directly used for calculations. Point-in-time reconstruction (Phase 3) replays audit entries to reverse-compute entity state, which may involve understanding field semantics defined in business rules.
- `shared/ACCESS-MATRIX.md` — Audit viewer access: CEO/CTO have full history access; DM/PM can view audit entries for own portfolio entities only; other roles have no direct audit log access.
