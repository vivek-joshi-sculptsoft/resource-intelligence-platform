# Client Management — Dependencies

## Must Be Built Before This Module

| Module | What's Needed | Why |
|---|---|---|
| 01-auth-and-roles | Access control middleware, Role entity, User entity | Every client API endpoint must check RolePermission before returning data. CEO/CTO have EDIT ALL; DM/PM have VIEW OWN_PORTFOLIO; Finance/HR have VIEW ALL; Engineer has NONE. |

## Modules That Depend on This Module

| Module | What They Need |
|---|---|
| 03-project-management | Client entity (`client_id` FK on Project). Every project belongs to a client. Client name and `is_active` status are used in project creation validation and display. |
| 07-utilization-dashboards | Client entity for client-level dashboard aggregations. Reads `id`, `name`, and `is_active` to group and display metrics per client. |
| 09-invoicing | Client entity indirectly via Project. Outstanding receivables are grouped by client. |
| 12-alerts | Client entity indirectly via Project. Contract expiry alerts reference the client through project data. |

## Shared References Used
- `shared/ENTITIES.md` — Defines the Client entity (section 2.4) owned by this module. Also references Project (section 2.6) and Assignment (section 2.7) from other modules, which are read to compute active project count and active resource count on the client detail view.
- `shared/BUSINESS-RULES.md` — Section 7.2 through 7.5 for Phase 2 financial aggregations on the client dashboard (total monthly billing, total cost, aggregate margin). Not used in Phase 1.
- `shared/ACCESS-MATRIX.md` — Defines access rules for the `client_profiles` data type: who can view/edit client data and at what scope.
