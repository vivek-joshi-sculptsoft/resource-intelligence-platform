# Master Entity Definitions

> **Single source of truth** for all field types, constraints, and relationships.
> Extracted from FSD §2 (Entity Definitions) and FSD §3 (Entity Relationships).
> Every module's `SCHEMA.md` references this file — entity definitions are NOT duplicated in module files.

## Notation (FSD §1)

> Fields marked with **\*** are required. Types: STRING, INTEGER, DECIMAL, DATE, TIMESTAMP, BOOLEAN, ENUM, FK (Foreign Key), TEXT. All monetary amounts: `DECIMAL(15,2)`. All percentages: INTEGER (0–100). PK = Primary Key. UK = Unique Key.

The system is built around **14 entities** (plus the `ResourceTag` join table).

---

## 2.1 Role

Configurable roles. New roles added without code changes. Granular access defined in RolePermission.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| name* | STRING(100) | Unique, not null | e.g., "CEO", "Delivery Manager", "Engineer" |
| code* | STRING(20) | Unique, not null | Machine key: CEO, CTO, DM, PM, FINANCE, HR, ENGINEER |
| permission_level* | INTEGER | Not null | Higher = more access. CEO=100, CTO=90, DM=70, PM=60, FINANCE=70, HR=50, ENGINEER=10 |
| is_active | BOOLEAN | Default: true | |
| created_at | TIMESTAMP | Auto | |

---

## 2.2 RolePermission

Granular access control: maps Role × Data Type → Access Level + Scope. Each row represents one cell from the PRD access matrix.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| role_id* | FK → Role | Not null | |
| data_type* | STRING(50) | Not null | What data this governs (see list below) |
| access_level* | ENUM | Not null | NONE, VIEW, EDIT |
| scope* | ENUM | Default: ALL | ALL, OWN_PORTFOLIO, SELF_ONLY |
| is_configurable | BOOLEAN | Default: false | If true, admin can override per user |

**Unique constraint:** (role_id, data_type) — one permission entry per data type per role.

**Data types (15):** `client_profiles`, `project_details`, `resource_profiles`, `allocation`, `billability`, `billing_rates`, `ctc_loaded_cost`, `project_margin`, `non_human_costs`, `shadow_assignments`, `resource_availability`, `bench_data`, `invoicing`, `worklogs`, `alerts`

> **Runtime Access Check**
> 1) Get user's role_id. 2) Look up RolePermission for role + data_type. 3) NONE = 403 or omit field. VIEW = read-only. EDIT = full access. 4) Apply scope: ALL = no filter, OWN_PORTFOLIO = filter by DM/PM assignment, SELF_ONLY = filter by own resource_id. 5) If is_configurable = true, check for user-level override (Phase 3).

See `ACCESS-MATRIX.md` for the full 105-row seed data.

---

## 2.3 User

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| email* | STRING(255) | Unique, not null | Login identifier |
| name* | STRING(255) | Not null | Display name |
| role_id* | FK → Role | Not null | References Role table |
| resource_id | FK → Resource | Nullable | Null for non-billable users (Finance, HR) |
| is_active | BOOLEAN | Default: true | Soft delete flag |
| created_at | TIMESTAMP | Auto | |
| updated_at | TIMESTAMP | Auto | |

---

## 2.4 Client

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| name* | STRING(255) | Unique, not null | |
| industry | STRING(100) | | |
| contact_name | STRING(255) | | Primary point of contact |
| contact_email | STRING(255) | | |
| contact_phone | STRING(20) | | |
| engagement_start_date | DATE | | |
| notes | TEXT | | |
| is_active | BOOLEAN | Default: true | |
| created_at | TIMESTAMP | Auto | |

---

## 2.5 Resource

An employee assignable to projects. Distinct from User — holds profile, cost, and skills data.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| employee_id* | STRING(50) | Unique, not null | Company employee ID |
| name* | STRING(255) | Not null | |
| designation* | STRING(100) | Not null | Primary designation. Can be overridden per project at Assignment level. |
| technical_expertise | STRING(100) | Nullable | Primary expertise. Overridable per project. |
| date_of_joining | DATE | | |
| reporting_manager_id | FK → Resource | Nullable | Self-referencing. CEO has null. |
| loaded_cost_monthly | DECIMAL(15,2) | Nullable | CTC + overhead/month in INR. **Phase 2.** Restricted to CEO/CTO/Finance. |
| is_active | BOOLEAN | Default: true | |
| created_at | TIMESTAMP | Auto | |

### ResourceTag (join table)

| Field | Type | Notes |
|---|---|---|
| resource_id* | FK → Resource | Composite PK |
| tag* | STRING(100) | Composite PK. e.g., "AWS Certified", "Healthcare Domain" |

---

## 2.6 Project

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| name* | STRING(255) | Not null | |
| client_id* | FK → Client | Not null | |
| type* | ENUM | Not null | FIXED_PRICE, TIME_AND_MATERIAL, CLIENT_ONBOARDING |
| billing_currency* | STRING(3) | Default: INR | ISO 4217: USD, EUR, GBP, INR |
| contract_value | DECIMAL(15,2) | | In billing_currency. Required for FIXED_PRICE. **Phase 2.** |
| start_date | DATE | | |
| contract_end_date | DATE | | Required for T&M and ONBOARDING. Expiry alerts. |
| dm_id* | FK → Resource | Not null | Delivery Manager |
| pm_id* | FK → Resource | Not null | Project Manager |
| worklog_enabled | BOOLEAN | Default: false | Toggle for employee worklog |
| notes | TEXT | | |
| status* | ENUM | Default: ACTIVE | ACTIVE, COMPLETED, ON_HOLD, CANCELLED |
| created_at | TIMESTAMP | Auto | |

---

## 2.7 Assignment (Core Entity)

Central entity mapping resource to project with allocation, billability, time bounds, and project-specific role.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| project_id* | FK → Project | Not null | |
| resource_id* | FK → Resource | Not null | |
| allocation_pct* | INTEGER | 1–100, not null | Capacity consumed by this project |
| billability_pct* | INTEGER | 0–100, not null | Must be ≤ allocation_pct |
| is_shadow* | BOOLEAN | Default: false | If true, billability_pct must be 0 |
| project_designation | STRING(100) | Nullable | Role on THIS project. Falls back to resource.designation if null. |
| project_expertise | STRING(100) | Nullable | Falls back to resource.technical_expertise if null. |
| billing_rate | DECIMAL(10,2) | Nullable | Per-hour in project billing_currency. Null for shadow. **Phase 2.** |
| start_date* | DATE | Not null | When assignment begins |
| end_date | DATE | Nullable | If set, auto-releases. If null, runs indefinitely. |
| status* | ENUM | Default: ACTIVE | ACTIVE, RELEASED, AUTO_RELEASED |
| released_at | TIMESTAMP | Nullable | When assignment actually ended |
| created_at | TIMESTAMP | Auto | |
| updated_at | TIMESTAMP | Auto | |

> **Constraint: Total Allocation**
> System does NOT hard-block >100% total allocation. Raises over-allocation alert instead. UI shows warning when total exceeds 100%.

> **Designation Resolution**
> Display: use assignment.project_designation if set, else resource.designation. Same for expertise. All views, search, and filters must respect this fallback order.

---

## 2.8 Milestone (Fixed Price Only)

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| project_id* | FK → Project | Not null | Must be FIXED_PRICE type |
| name* | STRING(255) | Not null | |
| amount* | DECIMAL(15,2) | Not null | In project billing_currency |
| planned_delivery_date | DATE | | |
| actual_delivery_date | DATE | | Set when status → DELIVERED |
| status* | ENUM | Default: PLANNED | PLANNED, DELIVERED, APPROVED, INVOICED, PAID |
| sort_order | INTEGER | | Display ordering |
| created_at | TIMESTAMP | Auto | |

---

## 2.9 Invoice

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| project_id* | FK → Project | Not null | |
| milestone_id | FK → Milestone | Nullable | Set for FP milestone invoices |
| invoice_date* | DATE | Not null | |
| billing_period_start | DATE | | For T&M/Onboarding monthly invoices |
| billing_period_end | DATE | | |
| amount* | DECIMAL(15,2) | Not null | In billing_currency. Actual revenue. |
| currency* | STRING(3) | Not null | Copied from project at invoice time |
| exchange_rate* | DECIMAL(10,4) | Default: 1.0 | Manual. 1 unit currency = X INR. Auto 1.0 for INR. |
| amount_inr* | DECIMAL(15,2) | Computed | = amount × exchange_rate |
| status* | ENUM | Default: DRAFT | DRAFT, SUBMITTED, APPROVED, PAID |
| notes | TEXT | | |
| created_at | TIMESTAMP | Auto | |

---

## 2.10 NonHumanCost

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| project_id* | FK → Project | Not null | |
| description* | STRING(500) | Not null | |
| category* | ENUM | Not null | AI_TOOLS, CLOUD_INFRA, DEVICES, THIRD_PARTY_LICENSE, OTHER |
| amount* | DECIMAL(15,2) | Not null | In original currency |
| currency* | STRING(3) | Default: INR | ISO 4217 code |
| exchange_rate* | DECIMAL(10,4) | Default: 1.0 | Manual. Auto 1.0 for INR. |
| amount_inr* | DECIMAL(15,2) | Computed | = amount × exchange_rate |
| cost_date* | DATE | Not null | When incurred |
| is_recurring* | BOOLEAN | Default: false | |
| recurring_end_date | DATE | | Required if is_recurring = true |
| created_by | FK → User | | |
| created_at | TIMESTAMP | Auto | |

---

## 2.11 Worklog (Optional)

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| resource_id* | FK → Resource | Not null | |
| project_id* | FK → Project | Not null | Must have active assignment AND worklog_enabled |
| log_date* | DATE | Not null | Cannot be in the future |
| hours* | DECIMAL(4,1) | 0.5–24.0 | Half-hour increments |
| note | TEXT | | Optional description |
| created_at | TIMESTAMP | Auto | |

> **Decoupled by Design**
> Worklog has NO FK or trigger relationship with Invoice, Assignment billability, or any financial entity. Purely informational. Deleting a worklog has zero side effects.

---

## 2.12 AuditLog

Immutable. Never updated or deleted — append only.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | BIGINT | PK, auto-increment | |
| entity_type* | STRING(50) | Not null | "Assignment", "Milestone", "Invoice" |
| entity_id* | UUID | | ID of changed record |
| action* | ENUM | | CREATE, UPDATE, DELETE |
| field_name | STRING(100) | | Which field changed |
| old_value | TEXT | | Previous value (serialized) |
| new_value | TEXT | | New value (serialized) |
| changed_by* | FK → User | | Who |
| changed_at* | TIMESTAMP | | When |

---

## 2.13 Alert

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| type* | STRING(50) | Not null | CONTRACT_EXPIRY, BENCH_DURATION, OVER_ALLOCATION, etc. |
| severity* | ENUM | Default: INFO | INFO, WARNING, CRITICAL |
| title* | STRING(255) | Not null | Short summary |
| message* | TEXT | Not null | Detailed content |
| recipient_user_id* | FK → User | Not null | One row per recipient per event |
| entity_type | STRING(50) | Nullable | For deep-linking |
| entity_id | UUID | Nullable | |
| is_read | BOOLEAN | Default: false | |
| is_dismissed | BOOLEAN | Default: false | |
| created_at* | TIMESTAMP | Auto | |

---

## 2.14 SystemConfig

Key-value store for configurable thresholds. Eliminates hardcoded magic numbers.

| Key | Default | Description |
|---|---|---|
| alert.contract_expiry_days | 30 | Days before contract end for first alert |
| alert.contract_expiry_urgent_days | 7 | Days before contract end for urgent alert |
| alert.bench_threshold_days | 7 | Days on bench before alerting |
| alert.utilization_threshold_pct | 70 | Company utilization below this triggers alert |
| system.working_days_per_month | 22 | Used in revenue/utilization calculations |
| system.working_hours_per_day | 8 | Used in hourly revenue calculations |
| system.default_currency | INR | Default billing currency for new projects |

---

## 3. Entity Relationships (FSD §3)

| Relationship | Cardinality | Notes |
|---|---|---|
| Role → User | 1 : N | A role assigned to many users |
| Role → RolePermission | 1 : N | One permission entry per data_type per role |
| Client → Project | 1 : N | Multiple projects of different types |
| Project → Assignment | 1 : N | Many resource assignments |
| Resource → Assignment | 1 : N | Multiple concurrent assignments (split allocation) |
| Project → Milestone | 1 : N | Only for FIXED_PRICE projects |
| Project → Invoice | 1 : N | Multiple invoices over lifetime |
| Milestone → Invoice | 1 : 0..1 | A milestone may have one invoice |
| Project → NonHumanCost | 1 : N | Many cost line items |
| Project → Worklog | 1 : N | Only if worklog_enabled = true |
| Resource → Worklog | 1 : N | Resource logs against assigned projects |
| Resource → Resource | N : 1 | Self-referencing (reporting_manager_id) |
| User → Alert | 1 : N | One alert row per recipient per event |

---

## Entity Ownership Map (one owning module per entity)

| Entity | Owning Module |
|---|---|
| Role | 01-auth-and-roles |
| RolePermission | 01-auth-and-roles |
| User | 01-auth-and-roles |
| Resource | 04-resource-management |
| ResourceTag | 04-resource-management |
| Client | 02-client-management |
| Project | 03-project-management |
| Assignment | 05-allocation-tracking |
| NonHumanCost | 06-non-human-costs |
| Milestone | 09-invoicing |
| Invoice | 09-invoicing |
| Worklog | 11-worklog |
| Alert | 12-alerts |
| SystemConfig | 12-alerts |
| AuditLog | 13-audit-history |

> Fields `loaded_cost_monthly` (Resource) and `billing_rate` (Assignment) are owned by their respective base modules but are introduced/activated by **08-financial-engine** in Phase 2.
