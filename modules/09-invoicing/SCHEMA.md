# Module 09: Invoicing — Schema

## Entities Owned by This Module

### Milestone (FSD §2.8)

Full definition in `shared/ENTITIES.md §2.8`. Fixed Price projects only.

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| project_id* | FK → Project | Must be FIXED_PRICE type |
| name* | STRING(255) | |
| amount* | DECIMAL(15,2) | In project billing_currency; must be > 0 |
| planned_delivery_date | DATE | |
| actual_delivery_date | DATE NULLABLE | Set when status → DELIVERED |
| status* | ENUM(PLANNED, DELIVERED, APPROVED, INVOICED, PAID) DEFAULT PLANNED | |
| sort_order | INTEGER | Display ordering |
| created_at | TIMESTAMP AUTO | |

**DB indexes:** `project_id`, `status`, `planned_delivery_date`

### Invoice (FSD §2.9)

Full definition in `shared/ENTITIES.md §2.9`.

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| project_id* | FK → Project | |
| milestone_id | FK → Milestone NULLABLE | Set for FP milestone invoices |
| invoice_date* | DATE | |
| billing_period_start | DATE NULLABLE | T&M/Onboarding monthly invoices |
| billing_period_end | DATE NULLABLE | |
| amount* | DECIMAL(15,2) | In billing_currency; must be > 0 |
| currency* | STRING(3) | Copied from project at invoice time |
| exchange_rate* | DECIMAL(10,4) DEFAULT 1.0 | Manual; auto 1.0 for INR |
| amount_inr* | DECIMAL(15,2) COMPUTED | = amount × exchange_rate |
| status* | ENUM(DRAFT, SUBMITTED, APPROVED, PAID) DEFAULT DRAFT | |
| notes | TEXT NULLABLE | |
| created_at | TIMESTAMP AUTO | |

**DB indexes:** `project_id`, `milestone_id`, `status`, `invoice_date`

---

## Entities Referenced from Other Modules

### Project (owned by Module 03)
Fields used: `id`, `name`, `type`, `client_id`, `billing_currency`, `status`

See `shared/ENTITIES.md §2.6`.
