# Module 03: Project Management — Schema

## Entities Owned by This Module

### Project (FSD §2.6)

Full definition in `shared/ENTITIES.md §2.6`.

| Field | Type | Phase | Notes |
|---|---|---|---|
| id* | UUID PK | 1 | |
| name* | STRING(255) | 1 | |
| client_id* | FK → Client | 1 | |
| type* | ENUM(FIXED_PRICE, TIME_AND_MATERIAL, CLIENT_ONBOARDING) | 1 | |
| billing_currency* | STRING(3) DEFAULT INR | 1 | ISO 4217 |
| contract_value | DECIMAL(15,2) | 2 | In billing_currency. Required for FIXED_PRICE. |
| start_date | DATE | 1 | |
| contract_end_date | DATE | 1 | Required for T&M and ONBOARDING |
| dm_id* | FK → Resource | 1 | Delivery Manager |
| pm_id* | FK → Resource | 1 | Project Manager |
| worklog_enabled | BOOLEAN DEFAULT false | 1 | Employee worklog toggle |
| notes | TEXT | 1 | |
| status* | ENUM(ACTIVE, COMPLETED, ON_HOLD, CANCELLED) DEFAULT ACTIVE | 1 | |
| created_at | TIMESTAMP AUTO | 1 | |

**DB indexes:** `client_id`, `dm_id`, `pm_id`, `status`

---

## Entities Referenced from Other Modules

### Client (owned by Module 02)

Fields used: `id`, `name`, `is_active`

See `shared/ENTITIES.md §2.4`.

### Resource (owned by Module 04)

Used for `dm_id` and `pm_id` lookups. Also used to display DM/PM names.

Fields used: `id`, `name`, `designation`

See `shared/ENTITIES.md §2.5`.

### Assignment (owned by Module 05)

Read to populate the assignments tab in project detail and to trigger auto-release when project is completed/cancelled.

Fields used: `id`, `resource_id`, `allocation_pct`, `billability_pct`, `is_shadow`, `status`, `start_date`, `end_date`

See `shared/ENTITIES.md §2.7`.
