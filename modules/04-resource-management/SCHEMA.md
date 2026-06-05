# Module 04: Resource Management — Schema

## Entities Owned by This Module

### Resource (FSD §2.5)

Full definition in `shared/ENTITIES.md §2.5`.

| Field | Type | Phase | Notes |
|---|---|---|---|
| id* | UUID PK | 1 | |
| employee_id* | STRING(50) UNIQUE | 1 | Company employee ID |
| name* | STRING(255) | 1 | |
| designation* | STRING(100) | 1 | Primary. Can be overridden per project in Assignment. |
| technical_expertise | STRING(100) NULLABLE | 1 | Primary expertise. Overridable per project. |
| date_of_joining | DATE | 1 | |
| reporting_manager_id | FK → Resource NULLABLE | 1 | Self-referencing. CEO has null. |
| loaded_cost_monthly | DECIMAL(15,2) NULLABLE | 2 | CTC + overhead/month in INR. Restricted to CEO/CTO/Finance. |
| is_active | BOOLEAN DEFAULT true | 1 | Soft delete |
| created_at | TIMESTAMP AUTO | 1 | |

**DB indexes:** `employee_id`, `is_active`, `designation`, `reporting_manager_id`

### ResourceTag (join table, FSD §2.5)

Full definition in `shared/ENTITIES.md §2.5`.

| Field | Type | Notes |
|---|---|---|
| resource_id* | FK → Resource | Composite PK |
| tag* | STRING(100) | Composite PK |

**DB indexes:** `resource_id`, `tag` (for tag-based search)

---

## Entities Referenced from Other Modules

### Assignment (owned by Module 05)

Read to show a resource's current assignments, total allocation, and assignment history on the resource profile.

Fields used: `id`, `project_id`, `allocation_pct`, `billability_pct`, `is_shadow`, `project_designation`, `project_expertise`, `billing_rate`, `start_date`, `end_date`, `status`, `released_at`

See `shared/ENTITIES.md §2.7`.

### Project (owned by Module 03)

Used to display project name and client in the resource's assignments list.

Fields used: `id`, `name`, `client_id`, `type`, `billing_currency`

See `shared/ENTITIES.md §2.6`.

### User (owned by Module 01)

Used to link a resource to a login account.

Fields used: `id`, `resource_id`, `role_id`

See `shared/ENTITIES.md §2.3`.
