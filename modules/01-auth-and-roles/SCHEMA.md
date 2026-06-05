# Module 01: Auth & Roles — Schema

## Entities Owned by This Module

Full definitions in `shared/ENTITIES.md`. This module **creates and owns** Role, RolePermission, and User.

### Role (FSD §2.1)

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| name* | STRING(100) UNIQUE | "CEO", "Delivery Manager", etc. |
| code* | STRING(20) UNIQUE | CEO, CTO, DM, PM, FINANCE, HR, ENGINEER |
| permission_level* | INTEGER | CEO=100, CTO=90, DM=70, PM=60, FINANCE=70, HR=50, ENGINEER=10 |
| is_active | BOOLEAN DEFAULT true | |
| created_at | TIMESTAMP AUTO | |

### RolePermission (FSD §2.2)

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| role_id* | FK → Role | |
| data_type* | STRING(50) | 15 allowed values (see below) |
| access_level* | ENUM(NONE,VIEW,EDIT) | |
| scope* | ENUM(ALL,OWN_PORTFOLIO,SELF_ONLY) DEFAULT ALL | |
| is_configurable | BOOLEAN DEFAULT false | |

Unique constraint: (role_id, data_type).

Allowed data_type values: `client_profiles`, `project_details`, `resource_profiles`, `allocation`, `billability`, `billing_rates`, `ctc_loaded_cost`, `project_margin`, `non_human_costs`, `shadow_assignments`, `resource_availability`, `bench_data`, `invoicing`, `worklogs`, `alerts`

### User (FSD §2.3)

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| email* | STRING(255) UNIQUE | Login identifier |
| name* | STRING(255) | |
| role_id* | FK → Role | |
| resource_id | FK → Resource NULLABLE | Null for Finance, HR |
| is_active | BOOLEAN DEFAULT true | Soft delete |
| created_at | TIMESTAMP AUTO | |
| updated_at | TIMESTAMP AUTO | |

### SystemConfig (partial — Phase 1 keys only)

Owned by Module 12 (Alerts) but seeded here for Phase 1 operation:

| Key | Default |
|---|---|
| system.working_days_per_month | 22 |
| system.working_hours_per_day | 8 |
| system.default_currency | INR |

---

## Entities Referenced from Other Modules

### Resource (owned by Module 04)

Used only to link `User.resource_id` to the resource profile. Only `id` and `name` are needed at auth time.

See `shared/ENTITIES.md §2.5` for full definition.
