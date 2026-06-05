# Module 06: Non-Human Costs — Schema

## Entities Owned by This Module

### NonHumanCost (FSD §2.10)

Full definition in `shared/ENTITIES.md §2.10`.

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| project_id* | FK → Project | |
| description* | STRING(500) | |
| category* | ENUM(AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER) | |
| amount* | DECIMAL(15,2) | In original currency; must be > 0 |
| currency* | STRING(3) DEFAULT INR | ISO 4217 |
| exchange_rate* | DECIMAL(10,4) DEFAULT 1.0 | Auto 1.0 for INR |
| amount_inr* | DECIMAL(15,2) COMPUTED | = amount × exchange_rate |
| cost_date* | DATE | When incurred |
| is_recurring* | BOOLEAN DEFAULT false | |
| recurring_end_date | DATE NULLABLE | Required if is_recurring = true |
| created_by | FK → User | |
| created_at | TIMESTAMP AUTO | |

**DB indexes:** `project_id`, `category`, `is_recurring`, `cost_date`

---

## Entities Referenced from Other Modules

### Project (owned by Module 03)
Fields used: `id`, `name`, `client_id`, `type`, `status`

See `shared/ENTITIES.md §2.6`.

### User (owned by Module 01)
Used for `created_by` field.

Fields used: `id`, `name`

See `shared/ENTITIES.md §2.3`.
