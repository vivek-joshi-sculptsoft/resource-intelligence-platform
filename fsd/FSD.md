# Functional Specification Document

## Resource Intelligence & Project Economics Platform

*Technical specifications — entity definitions, state machines, calculation logic, validation rules, and edge cases.*

| | |
|---|---|
| **Version** | 1.0 |
| **Date** | June 2026 |
| **Based On** | PRD v1.1 |
| **Audience** | Engineering Team |
| **Confidentiality** | Internal Use Only |

---

## 1. Introduction & Scope

This document translates the PRD v1.1 into developer-ready specifications. It defines the exact data model, business logic, validation rules, state machines, calculation formulas, and edge cases for the Resource Intelligence & Project Economics Platform.

Every field definition, validation, and formula in this document is authoritative. If there is any ambiguity between the PRD and this FSD, the FSD takes precedence for implementation.

> **Notation**
> Fields marked with **\*** are required. Types: STRING, INTEGER, DECIMAL, DATE, TIMESTAMP, BOOLEAN, ENUM, FK (Foreign Key), TEXT. All monetary amounts: DECIMAL(15,2). All percentages: INTEGER (0–100). PK = Primary Key. UK = Unique Key.

---

## 2. Entity Definitions

The system is built around 14 entities.

### 2.1 Role

Configurable roles. New roles added without code changes. Granular access defined in RolePermission.

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| name* | STRING(100) | Unique, not null | e.g., "CEO", "Delivery Manager", "Engineer" |
| code* | STRING(20) | Unique, not null | Machine key: CEO, CTO, DM, PM, FINANCE, HR, ENGINEER |
| permission_level* | INTEGER | Not null | Higher = more access. CEO=100, CTO=90, DM=70, PM=60, FINANCE=70, HR=50, ENGINEER=10 |
| is_active | BOOLEAN | Default: true | |
| created_at | TIMESTAMP | Auto | |

### 2.2 RolePermission

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

**Data types:** `client_profiles`, `project_details`, `resource_profiles`, `allocation`, `billability`, `billing_rates`, `ctc_loaded_cost`, `project_margin`, `non_human_costs`, `shadow_assignments`, `resource_availability`, `bench_data`, `invoicing`, `worklogs`, `alerts`

**Seed data (examples):**

| Role | data_type | access_level | scope | is_configurable |
|---|---|---|---|---|
| CEO | ctc_loaded_cost | VIEW | ALL | false |
| DM | billing_rates | VIEW | OWN_PORTFOLIO | true |
| PM | allocation | EDIT | OWN_PORTFOLIO | false |
| PM | ctc_loaded_cost | NONE | — | false |
| Finance | invoicing | EDIT | ALL | false |
| Engineer | resource_availability | VIEW | ALL | false |
| Engineer | worklogs | EDIT | SELF_ONLY | false |

> **Runtime Access Check**
> 1) Get user's role_id. 2) Look up RolePermission for role + data_type. 3) NONE = 403 or omit field. VIEW = read-only. EDIT = full access. 4) Apply scope: ALL = no filter, OWN_PORTFOLIO = filter by DM/PM assignment, SELF_ONLY = filter by own resource_id. 5) If is_configurable = true, check for user-level override (Phase 3).

### 2.3 User

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

### 2.4 Client

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

### 2.5 Resource

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
| loaded_cost_monthly | DECIMAL(15,2) | Nullable | CTC + overhead/month in INR. Phase 2. Restricted to CEO/CTO/Finance. |
| is_active | BOOLEAN | Default: true | |
| created_at | TIMESTAMP | Auto | |

**ResourceTag** (join table):

| Field | Type | Notes |
|---|---|---|
| resource_id* | FK → Resource | Composite PK |
| tag* | STRING(100) | Composite PK. e.g., "AWS Certified", "Healthcare Domain" |

### 2.6 Project

| Field | Type | Constraints | Notes |
|---|---|---|---|
| id* | UUID | PK | |
| name* | STRING(255) | Not null | |
| client_id* | FK → Client | Not null | |
| type* | ENUM | Not null | FIXED_PRICE, TIME_AND_MATERIAL, CLIENT_ONBOARDING |
| billing_currency* | STRING(3) | Default: INR | ISO 4217: USD, EUR, GBP, INR |
| contract_value | DECIMAL(15,2) | | In billing_currency. Required for FIXED_PRICE. |
| start_date | DATE | | |
| contract_end_date | DATE | | Required for T&M and ONBOARDING. Expiry alerts. |
| dm_id* | FK → Resource | Not null | Delivery Manager |
| pm_id* | FK → Resource | Not null | Project Manager |
| worklog_enabled | BOOLEAN | Default: false | Toggle for employee worklog |
| notes | TEXT | | |
| status* | ENUM | Default: ACTIVE | ACTIVE, COMPLETED, ON_HOLD, CANCELLED |
| created_at | TIMESTAMP | Auto | |

### 2.7 Assignment (Core Entity)

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
| billing_rate | DECIMAL(10,2) | Nullable | Per-hour in project billing_currency. Null for shadow. Phase 2. |
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

### 2.8 Milestone (Fixed Price Only)

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

### 2.9 Invoice

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

### 2.10 NonHumanCost

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

### 2.11 Worklog (Optional)

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

### 2.12 AuditLog

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

### 2.13 Alert

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

### 2.14 SystemConfig

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

## 3. Entity Relationships

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

## 4. ER Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ RBAC                                                         │
│                                                              │
│  ┌──────────┐  1:N   ┌─────────────────┐                   │
│  │   Role   │───────→│ RolePermission  │                   │
│  └──────────┘        │ data_type       │                   │
│       │ 1:N          │ access_level    │                   │
│       ▼              │ scope           │                   │
│  ┌──────────┐        └─────────────────┘                   │
│  │   User   │                                               │
│  └──────────┘                                               │
└──────┬──────────────────────────────────────────────────────┘
       │ linked to
       ▼
┌─────────────────────────────────────────────────────────────┐
│ CORE                                                         │
│                                                              │
│  ┌──────────┐  1:N   ┌──────────────────┐   ┌────────────┐ │
│  │  Client  │───────→│    Project       │   │  Resource  │ │
│  └──────────┘        │ type, currency   │   │ designation│ │
│                      │ dm_id, pm_id     │   │ loaded_cost│ │
│                      └────────┬─────────┘   └──────┬─────┘ │
│                               │ 1:N                │ 1:N   │
│                               ▼                    ▼       │
│                      ┌─────────────────────────────────┐   │
│                      │    ASSIGNMENT (Core Entity)      │   │
│                      │ allocation_pct, billability_pct  │   │
│                      │ is_shadow, project_designation   │   │
│                      │ billing_rate, start/end_date     │   │
│                      └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
       │
       ├── Project 1:N ──→ Milestone (FP) ──1:0..1──→ Invoice
       ├── Project 1:N ──→ Invoice (T&M/Onboarding)
       ├── Project 1:N ──→ NonHumanCost
       └── Project 1:N ──→ Worklog ←── Resource 1:N

┌─────────────────────────────────────────────────────────────┐
│ SYSTEM: AuditLog, Alert, SystemConfig                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Diagram (Level 1)

```
┌────────┐  assignments    ┌─────────────────────┐
│   PM   │────────────────→│ P1 Allocation Mgmt  │──────→ D1 Assignments
└────────┘                 └─────────────────────┘
┌────────┐  decisions      ┌─────────────────────┐
│ DM/CTO │────────────────→│ P2 Project & Client │──────→ D2 Projects
└────────┘                 └─────────────────────┘
┌────────┐  ←dashboards→   ┌─────────────────────┐ reads
│CEO/CTO │←───────────────→│ P3 Reporting        │- - -→ D1, D2, D3
└────────┘                 └─────────────────────┘
┌────────┐  invoices,rates ┌─────────────────────┐
│Finance │────────────────→│ P4 Financial Proc.  │──────→ D3 Invoices & Costs
└────────┘                 └─────────────────────┘
┌────────┐  daily hours    ┌─────────────────────┐
│Engineer│────────────────→│ P5 Worklog Mgmt     │──────→ D4 Worklogs
└────────┘                 └─────────────────────┘

┌───────────┐  daily       ┌─────────────────────┐
│ Scheduler │─────────────→│ P6 Alert Engine     │──────→ D6 Alerts
│           │─────────────→│ P7 Auto-Release Job │──────→ D1 (release)
└───────────┘              └─────────────────────┘

All writes ──────────────────────────────→ D5 Audit Log
```

---

## 6. State Machines & Lifecycles

### 6.1 Assignment Lifecycle

```
[ACTIVE] ──manual──→ [RELEASED]
[ACTIVE] ──auto-job──→ [AUTO_RELEASED]
```

| Transition | Trigger | Side Effects |
|---|---|---|
| ACTIVE → RELEASED | PM manually releases | Set released_at = now(). Recalculate total allocation. If before end_date, log as early release. |
| ACTIVE → AUTO_RELEASED | Daily job: end_date ≤ today | Set released_at = end_date midnight. Fire alert to PM and DM. Recalculate total allocation. |

### 6.2 Milestone Lifecycle (Fixed Price)

```
[PLANNED] → [DELIVERED] → [APPROVED] → [INVOICED] → [PAID]
```

| Transition | Who | Side Effects |
|---|---|---|
| PLANNED → DELIVERED | PM | Set actual_delivery_date. Flag delay if actual > planned. |
| DELIVERED → APPROVED | PM/DM | Client approved the deliverable |
| APPROVED → INVOICED | Finance | Creates Invoice with amount, exchange_rate, amount_inr |
| INVOICED → PAID | Finance | Updates Invoice status to PAID |

> **Backward Transitions**
> DELIVERED can revert to PLANNED (rejected). APPROVED can revert to DELIVERED (withdrawn). INVOICED and PAID are terminal. For corrections, create credit note (negative invoice).

### 6.3 Invoice Lifecycle

```
[DRAFT] → [SUBMITTED] → [APPROVED] → [PAID]
```

For T&M: DRAFT at month-end, SUBMITTED to client, APPROVED = confirmed, PAID = received.

### 6.4 Project Status

```
[ACTIVE] → [COMPLETED]
[ACTIVE] ⇄ [ON_HOLD]
[ACTIVE] → [CANCELLED]
```

When COMPLETED or CANCELLED: all ACTIVE assignments auto-released. No new assignments can be created.

---

## 7. Calculations & Business Logic

### 7.1 Resource Utilization

```
Total Allocation (resource) = SUM(allocation_pct) across all ACTIVE assignments
Billable Allocation (resource) = SUM(billability_pct) where is_shadow = false
Utilization Rate (resource) = Billable Allocation / 100 × 100%
Company Utilization = SUM(all billable alloc) / (active_resource_count × 100) × 100%
```

### 7.2 Project Cost (Monthly)

```
Resource Cost = SUM(loaded_cost_monthly × allocation_pct / 100) for all ACTIVE assignments
Non-Human Cost (INR) = SUM(amount_inr for one-time in month) + SUM(amount_inr for active recurring)
Total Project Cost = Resource Cost + Non-Human Cost
```

Shadow resources contribute to cost but NOT to projected revenue.

### 7.3 Projected Revenue (Monthly)

```
Per Assignment = billability_pct / 100 × working_days × 8 × billing_rate
Project Projected Revenue = SUM(per-assignment) for non-shadow ACTIVE assignments
Projected Revenue INR = Projected Revenue × latest_exchange_rate (or 1.0 if INR)
```

Working days: default 22 from SystemConfig.

### 7.4 Actual Revenue

```
Actual Revenue (project, period) = SUM(invoice.amount_inr) where status ∈ {APPROVED, PAID}
```

Source of truth for financial reporting. Not calculated from allocation.

### 7.5 Margin

```
Projected Margin = Projected Revenue (INR) − Total Project Cost
Actual Margin = Actual Revenue (INR) − Total Project Cost
Margin % = Margin / Revenue × 100
```

Client-level: sum across all projects. Company-level: sum across all projects.

### 7.6 Bench Cost

```
Daily Bench Cost = loaded_cost_monthly / 22
Total Bench Cost = Daily Cost × days_on_bench
```

Bench start = max(released_at) of last assignment, or date_of_joining if never assigned.

### 7.7 Exchange Rate Conversion

```
amount_inr = amount × exchange_rate
```

Exchange rate = 1 unit of billing currency = X INR. Manually entered. Auto 1.0 for INR.

---

## 8. Auto-Release Logic

Scheduled daily job (midnight IST). Processes all assignments where end_date ≤ today and status = ACTIVE.

```
FOR EACH assignment WHERE status = 'ACTIVE' AND end_date IS NOT NULL AND end_date <= TODAY:
    SET assignment.status = 'AUTO_RELEASED'
    SET assignment.released_at = end_date + '23:59:59'
    CREATE alert(type: 'ASSIGNMENT_AUTO_RELEASED', recipients: [PM, DM])
    INSERT INTO audit_log(...)
```

> **Edge Case: Extension on Release Day**
> If PM extends end_date before the job runs, the job skips that assignment (end_date is now in the future). If the job already ran, PM must create a new assignment.

---

## 9. View Specifications

### Company Dashboard (CEO, CTO)

| Widget | Data | Calculation |
|---|---|---|
| Billable Utilization | Single number + trend | §7.1 Company Utilization |
| Bench Count | Count + names | Resources with 0 ACTIVE assignments |
| Shadow Allocation | Count + total % | SUM(allocation_pct) where is_shadow = true |
| Revenue Summary | Projected vs Actual (INR) | §7.3 and §7.4 aggregated |
| Active Projects | Count by type | GROUP BY type WHERE status = ACTIVE |
| Upcoming Releases | Next 30 days | Assignments with end_date in next 30 days |
| Overdue Milestones | Count + list | planned_date < today AND status = PLANNED |

### Project Detail View (PM own, DM portfolio, CTO/CEO all)

| Section | Data | Actions |
|---|---|---|
| Header | Name, client, type, status, billing currency, DM, PM | Edit project details (PM+) |
| Resource Assignments | Table: name, project designation (or default), allocation %, billability %, shadow, rate, dates, status | Add/edit/release (PM) |
| Non-Human Costs | Table: date, description, category, amount, currency, rate, INR, recurring | Add/edit/delete (PM+) |
| Milestones (FP) | Table: name, amount, planned date, status, actual date | Add/edit milestone, transition status (PM) |
| Invoices | Table: date, amount, currency, rate, INR, status | Create invoice (Finance) |
| Financials (restricted) | Projected revenue, actual revenue, resource cost, non-human cost, margins | View only (CEO/CTO/Finance) |
| Worklogs | Table: date, resource, hours, note. Only if worklog_enabled. | View (PM+) |

### Resource Availability View (ALL users including engineers)

| Section | Data |
|---|---|
| Currently on Bench | Resource name, designation, expertise, days on bench, tags |
| Partially Available | Name, total allocation %, spare capacity %, project names |
| Releasing Soon | Name, project, allocation %, release date, days remaining (30/60/90 filters) |
| Fully Allocated | Name, total allocation %, project names |

> **What Everyone Can See**
> Project names and allocation % are visible. Billing rates, billability %, CTC, and shadow status are NOT visible to Engineers.

### My Assignments — Engineer View (own data only)

| Section | Data | Actions |
|---|---|---|
| Active Assignments | Project name, client, allocation %, start date, end date | View only |
| Worklog Entry | For projects with worklog_enabled: date, hours, note | Add/edit own worklogs |
| Worklog History | Past 30 days of own entries | Edit own entries |

---

## 10. Access Control Rules

Enforced at API level. Every endpoint checks user's role (via role_id → Role) and scope.

### Scope Rules

| Role | Project Scope | Resource Scope |
|---|---|---|
| CEO, CTO | All projects | All resources |
| Finance | All (financial data only) | All (cost data only) |
| DM | project.dm_id = current user | Resources on DM's projects |
| PM | project.pm_id = current user | Resources on PM's projects |
| HR | All (profiles only) | All (profiles, no financials) |
| Engineer | Own ACTIVE assignments | Self + availability view (all) |

### Field-Level Restrictions

| Field | Visible To | Enforcement |
|---|---|---|
| loaded_cost_monthly | CEO, CTO, Finance | API returns null for others |
| billing_rate | CEO, CTO, Finance, DM (configurable) | API returns null if restricted |
| billability_pct | CEO, CTO, Finance, DM, PM | Hidden from HR and Engineer |
| is_shadow | CEO, CTO, Finance, DM, PM | Hidden from HR and Engineer |
| All margin fields | CEO, CTO, Finance, DM (configurable) | Computed fields omitted |
| exchange_rate | CEO, CTO, Finance | Write access: Finance only |

---

## 11. Validation Rules

### Assignment Validations

| Rule | Condition | Error |
|---|---|---|
| Billability ≤ Allocation | billability_pct > allocation_pct | "Billability cannot exceed allocation percentage" |
| Shadow = zero billability | is_shadow = true AND billability_pct > 0 | "Shadow resources cannot have billability" |
| End after start | end_date ≤ start_date | "End date must be after start date" |
| No duplicate active | Same resource+project has ACTIVE assignment | "Resource already has an active assignment on this project" |
| Project must be active | project.status ≠ ACTIVE | "Cannot create assignment on a non-active project" |
| Allocation range | < 1 or > 100 | "Allocation must be between 1% and 100%" |
| Over-allocation | Total > 100% after this | Warning (not blocking): "This will bring total allocation to {X}%" |

### Invoice Validations

| Rule | Condition | Error |
|---|---|---|
| Amount positive | amount ≤ 0 | "Invoice amount must be positive" |
| Exchange rate positive | exchange_rate ≤ 0 | "Exchange rate must be positive" |
| INR auto-rate | currency = 'INR' | Auto-set exchange_rate = 1.0, disable field |
| FP milestone required | FIXED_PRICE and no milestone_id | "Fixed price invoices must be linked to a milestone" |
| Milestone approved | Linked milestone ≠ APPROVED | "Milestone must be approved before invoicing" |

### Non-Human Cost Validations

| Rule | Condition | Error |
|---|---|---|
| Amount positive | amount ≤ 0 | "Cost amount must be positive" |
| Exchange rate positive | exchange_rate ≤ 0 | "Exchange rate must be positive" |
| INR auto-rate | currency = 'INR' | Auto-set exchange_rate = 1.0, disable field |
| Recurring needs end date | is_recurring = true AND recurring_end_date is null | "Recurring costs must have an end date" |
| End after start | recurring_end_date ≤ cost_date | "Recurring end date must be after cost date" |

### Worklog Validations

| Rule | Condition | Error |
|---|---|---|
| Worklog enabled | project.worklog_enabled = false | "Worklog is not enabled for this project" |
| Active assignment | No ACTIVE assignment for resource on project | "You must have an active assignment to log hours" |
| No future dates | log_date > today | "Cannot log hours for future dates" |
| Hours range | < 0.5 or > 24 | "Hours must be between 0.5 and 24" |
| No duplicate | Same resource + project + log_date exists | "Entry already exists for this date. Edit the existing entry." |

### Designation Resolution

> **Fallback Rule**
> When displaying a resource's role on a project: use assignment.project_designation if set, else resource.designation. Same for expertise. All views, search, and filters must respect this.

---

## 12. Alert Specifications

All alerts in-app, stored in Alert table, dismissible. Thresholds from SystemConfig.

| Type | Trigger | Frequency | Recipients |
|---|---|---|---|
| CONTRACT_EXPIRY | End date within 30d (configurable) | Daily; fires at 30d and 7d | DM, CTO, CEO |
| BENCH_DURATION | Resource on bench > 7d (configurable) | Daily | DM, CTO, HR |
| OVER_ALLOCATION | Total allocation > 100% | On change | DM, PM |
| MILESTONE_OVERDUE | Planned date passed, status = PLANNED | Daily | PM, DM |
| UTILIZATION_DROP | Company util < 70% (configurable) | Weekly (Monday) | CTO, CEO |
| ASSIGNMENT_AUTO_RELEASED | Assignment auto-released by job | On release | PM, DM |

---

## 13. Audit & History

### Tracked Entities

| Entity | Tracked Fields |
|---|---|
| Assignment | ALL (allocation, billability, shadow, rate, designation, expertise, dates, status) |
| Milestone | status, planned_date, actual_date, amount |
| Invoice | amount, exchange_rate, status |
| Project | status, contract_end_date, contract_value |
| Resource | designation, loaded_cost, is_active |
| NonHumanCost | ALL fields |

### Historical Point-in-Time Query

To reconstruct state at a past date, replay the audit log backwards:

```
1. Get current state: SELECT * FROM entity WHERE id = X
2. Get all changes AFTER date D: SELECT * FROM audit_log
     WHERE entity_type = 'Assignment' AND entity_id = X AND changed_at > D
     ORDER BY changed_at DESC
3. For each change: current_state[field_name] = old_value
```

---

## 14. Edge Cases & Error Handling

| Scenario | Expected Behavior |
|---|---|
| Resource deactivated while assigned | All ACTIVE assignments released. Cannot receive new assignments. |
| Client deactivated with active projects | Block. "Complete or cancel all projects first." |
| Project completed with unpaid invoices | Allow. Unpaid invoices remain trackable. |
| PM extends end_date after auto-release | Cannot modify released assignment. Create new assignment. |
| Assignment start_date in future | Valid. ACTIVE but contributes to calcs only from start_date. |
| Recurring cost with no end date | Block. "Recurring costs must have end date." |
| Invoice for T&M with no active assignments | Allow. Handles retroactive billing. |
| Worklog after assignment ends | Block if no ACTIVE assignment on log_date. Allow backfill if was active then. |
| DM changed on project | New DM gains visibility. Old DM loses it. Audit logged. |
| Same resource reassigned after release | Allowed if previous is RELEASED/AUTO_RELEASED. One ACTIVE per resource per project. |
| All milestones paid but project still active | Valid. No auto-completion. |
| Exchange rate = 0 | Block. "Exchange rate must be positive." |
| Worklog hours > 24/day across projects | Warning (not blocking). Allow save. |

---

## 15. Phase-wise Implementation Guide

> **Principle**
> Each phase is fully functional on its own. Phase 1 replaces spreadsheets. Phase 2 adds financials. Phase 3 adds intelligence. Build order per phase: DB migrations → API → business logic → UI → validations → tests.

### Phase 1 — Foundation & Visibility

#### Entities

| Entity | Scope | Notes |
|---|---|---|
| Role + RolePermission | Full | Seed with 7 default roles and permissions |
| User | Full | Auth, login, role assignment |
| Client | Full | CRUD |
| Resource + Tags | Full except loaded_cost_monthly | Cost field is Phase 2 |
| Project | Full except contract_value | billing_currency exists but exchange rate logic is Phase 2 |
| Assignment | Full except billing_rate | Core allocation/billability with recurring model + auto-release |
| Worklog | Full | Optional per-project. Decoupled. |
| AuditLog | Full | Start logging from day 1 |
| SystemConfig | Partial | working_days, working_hours, default_currency only |

#### Features

- Auth and role-based access using RolePermission seed data
- Client, Project, Resource CRUD with full validations
- Assignment management: recurring carry-forward, auto-release job, shadow flagging, project-specific designations
- Utilization dashboards: company-wide, per-DM, per-client, per-project, per-resource (§7.1 formulas)
- Resource availability view: bench, partial, upcoming releases — visible to ALL including engineers
- My Assignments (engineer): personal view + worklog entry for enabled projects
- Audit logging for all Assignment, Project, Resource changes

### Phase 2 — Financial Engine

#### Entities

| Entity | Scope | Notes |
|---|---|---|
| Resource | Add loaded_cost_monthly | Enable cost calculations |
| Assignment | Add billing_rate | Per-resource per-project rate |
| Milestone | Full (new) | FIXED_PRICE only. Full lifecycle. |
| Invoice | Full (new) | Amount, currency, exchange rate, INR. Links to milestone. |
| NonHumanCost | Full (new) | Amount, currency, exchange rate, INR. One-time and recurring. |

#### Features

- Cost calculations: resource cost + non-human cost (§7.2)
- Projected revenue from billability × rate (§7.3)
- Actual revenue from invoice amounts (§7.4)
- Projected and actual margin (§7.5) at project, client, company levels
- Milestone management: CRUD, lifecycle, delivery delay detection
- Invoicing workflow: create with amount + exchange rate, status lifecycle
- Non-human cost management: CRUD with currency, exchange rate, INR conversion, recurring
- Multi-currency UI: show original + rate + INR side by side
- Financial dashboards for Finance, CEO, CTO
- Bench cost calculations (§7.6)

### Phase 3 — Intelligence & Alerts

#### Entities

| Entity | Scope | Notes |
|---|---|---|
| Alert | Full (new) | In-app notifications with deep-linking |
| SystemConfig | Full | All threshold keys, exposed in admin UI |
| UserPermissionOverride | Optional (new) | Per-user overrides for configurable permissions |

#### Features

- Alert engine: scheduled jobs for contract expiry, bench, milestone overdue, utilization drop (§12)
- Alert UI: notification panel, mark read/dismiss, deep-link to entity
- Configurable access: admin UI for RolePermission, per-user overrides
- Historical queries: point-in-time reconstruction from AuditLog (§13)
- Availability forecasting: 30/60/90 day views, auto-release-aware
- Admin settings UI for SystemConfig thresholds
- Audit log viewer: browse by entity, user, date range

> **Dependencies**
> Phase 2 depends on Phase 1 entities. Phase 3 depends on Phase 2 for financial data feeding alerts. Within each phase: DB migrations → API endpoints → business logic → UI views → validations → tests.

---

## Sign-Off

| Role | Name | Signature | Date |
|---|---|---|---|
| CTO | | | |
| Tech Lead | | | |
| Engineering Lead | | | |
| QA Lead | | | |
