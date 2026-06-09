# Entity Patterns & Conventions

Common patterns for entity design. Use these as defaults unless the domain requires otherwise.

---

## Naming Conventions

- **Entity names**: PascalCase singular (User, Project, Assignment — not Users, projects)
- **Field names**: snake_case (created_at, billing_rate, project_id)
- **FK fields**: `referenced_entity_id` (client_id, project_id, reporting_manager_id)
- **Boolean fields**: `is_` or `has_` prefix (is_active, is_shadow, has_attachment)
- **Date fields**: `_date` suffix for calendar dates (start_date, invoice_date), `_at` suffix for timestamps (created_at, released_at)
- **Status/type fields**: Use the entity's domain term (status, type, category — not state, kind, classification)
- **Monetary fields**: Include unit hint (amount, amount_inr, loaded_cost_monthly)

---

## Standard Field Patterns

### Every Entity Should Have
```
id          UUID/BIGINT    PK
created_at  TIMESTAMP      Auto, immutable
updated_at  TIMESTAMP      Auto, updates on every change
```

### Soft Delete
```
is_active   BOOLEAN        Default: true
```
Prefer `is_active` over `deleted_at` for simplicity. Use `deleted_at TIMESTAMP` only if you need to know *when* it was deleted.

### Audit-Ready Fields
```
created_by  FK → User      Who created this record
updated_by  FK → User      Who last modified it
```
These are cheap to add and valuable for debugging. Consider adding to high-change entities.

---

## Common Entity Templates

### Lookup/Reference Table
For values that could be ENUMs but need to be configurable:
```
id          UUID           PK
name        STRING(100)    Unique, not null (display name)
code        STRING(20)     Unique, not null (machine key for code references)
sort_order  INTEGER        For display ordering
is_active   BOOLEAN        Default: true
```
Examples: Role, Category, Status (when business needs to add new ones without code changes)

**When to use lookup table vs ENUM:**
- ENUM: ≤5 values that rarely change and are tightly coupled to code logic (assignment status: ACTIVE/RELEASED/AUTO_RELEASED)
- Lookup table: Values that business users might add/modify (roles, cost categories, industries)

### Join Table (Many-to-Many)
```
entity_a_id  FK → EntityA   Composite PK part 1
entity_b_id  FK → EntityB   Composite PK part 2
created_at   TIMESTAMP      When the association was created
```
Add extra columns if the relationship has attributes (e.g., ResourceTag has just resource_id + tag, but a ProjectMember might have role, start_date, etc.)

### Audit Log (Append-Only)
```
id            BIGINT AUTO    PK (BIGINT for performance on high-volume tables)
entity_type   STRING(50)     Which entity changed
entity_id     UUID           ID of the changed record
action        ENUM           CREATE, UPDATE, DELETE
field_name    STRING(100)    Which field (null for CREATE)
old_value     TEXT           Previous value, serialized
new_value     TEXT           New value, serialized
changed_by    FK → User      Who
changed_at    TIMESTAMP      When
```
**Rules**: Never UPDATE or DELETE rows. Use BIGINT PK for insert performance. Index on (entity_type, entity_id, changed_at).

### Config/Settings (Key-Value)
```
key           STRING(100)    PK
value         STRING(500)    Stored as string, parsed by app
description   STRING(255)    Human-readable explanation
updated_at    TIMESTAMP      When last changed
updated_by    FK → User      Who changed it
```

### Alert/Notification
```
id                UUID           PK
type              STRING(50)     Alert category code
severity          ENUM           INFO, WARNING, CRITICAL
title             STRING(255)    Short summary
message           TEXT           Detailed content
recipient_id      FK → User      One row per recipient per event
entity_type       STRING(50)     For deep-linking (nullable)
entity_id         UUID           For deep-linking (nullable)
is_read           BOOLEAN        Default: false
is_dismissed      BOOLEAN        Default: false
created_at        TIMESTAMP      When generated
```

---

## Money & Currency Pattern

When an entity deals with money in multiple currencies:
```
amount          DECIMAL(15,2)    Original amount
currency        STRING(3)        ISO 4217 code (USD, EUR, INR)
exchange_rate   DECIMAL(10,4)    Conversion rate to base currency
amount_base     DECIMAL(15,2)    Computed: amount × exchange_rate
```
- `exchange_rate` meaning: "1 unit of `currency` = X units of base currency"
- For base currency transactions (e.g., INR when base is INR), auto-set rate to 1.0
- Store `amount_base` for query performance (avoids runtime multiplication)
- The exchange rate is locked at transaction time — it doesn't float

---

## Percentage Pattern

Store as INTEGER (0-100), not DECIMAL (0.00-1.00):
- Business users think in "60%", not "0.60"
- Avoids floating-point precision issues
- Display: divide by 100 on the frontend
- Calculations: divide by 100 in formulas (`allocation_pct / 100 × loaded_cost`)

---

## Status/Lifecycle Pattern

For entities with state machines:
```
status          ENUM             Current state
status_changed_at TIMESTAMP     When status last changed (optional)
```

Design principles:
- Status values are past-tense or adjective (ACTIVE, COMPLETED, RELEASED — not COMPLETE, RELEASING)
- Terminal states cannot transition further (PAID, CANCELLED)
- Every transition needs: who can trigger it, what side effects fire
- Consider: does the entity need a full audit log, or just the current status?

---

## Anti-Patterns to Avoid

### The God Entity
An entity with 30+ fields covering multiple concerns. Split it:
- Bad: `Project` with 40 fields including financial, milestone, resource, and config data
- Good: `Project` (core) + `ProjectConfig` (settings) + `Milestone` (separate entity) + financial data computed from `Assignment` and `Invoice`

### Stringly-Typed Fields
Using STRING for everything:
- Bad: `status STRING(20)` — allows any value, no validation
- Good: `status ENUM(ACTIVE, COMPLETED, CANCELLED)` — constrained at DB level

### Implicit Relationships
Embedding related data as JSON in a text field:
- Bad: `tags TEXT` containing `"aws,python,healthcare"`
- Good: `ResourceTag` join table with proper FK and indexing

### Missing Timestamps
Entities without created_at/updated_at. Always add them — they're free and invaluable for debugging.

### Hardcoded Business Rules
Magic numbers in code instead of SystemConfig:
- Bad: `if (daysOnBench > 7)` hardcoded in the alert job
- Good: `if (daysOnBench > SystemConfig.get('alert.bench_threshold_days'))` — configurable without deployment

### ENUM Proliferation
Using ENUMs for everything including values that the business might add:
- Bad: `role ENUM('CEO','CTO','DM','PM','FINANCE','HR','ENGINEER')` — adding "Tech Architect" needs a migration
- Good: `role_id FK → Role` — adding roles is a data operation

---

## Index Recommendations

For every entity, consider indexes on:
- Foreign keys (most ORMs do this automatically)
- Status fields used in WHERE clauses
- Date fields used for range queries
- Composite indexes for common query patterns (e.g., `(resource_id, status)` for "get active assignments for resource")
- Unique constraints that aren't PKs (email, employee_id, code)

Don't over-index — each index slows writes. Profile actual queries before adding non-obvious indexes.
