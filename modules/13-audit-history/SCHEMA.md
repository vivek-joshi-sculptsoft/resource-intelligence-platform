# Module 13: Audit History — Schema

## Entities Owned by This Module

### AuditLog (FSD §2.12)

Full definition in `shared/ENTITIES.md §2.12`. **Immutable — append only.**

| Field | Type | Notes |
|---|---|---|
| id* | BIGINT PK, auto-increment | Integer PK (not UUID) for high-insert performance |
| entity_type* | STRING(50) | "Assignment", "Milestone", "Invoice", "Project", "Resource", "NonHumanCost" |
| entity_id* | UUID | ID of the changed record |
| action* | ENUM(CREATE, UPDATE, DELETE) | |
| field_name | STRING(100) | Which field changed (null for CREATE action header row) |
| old_value | TEXT | Previous value (JSON-serialized string); null for CREATE |
| new_value | TEXT | New value (JSON-serialized string); null for DELETE |
| changed_by* | FK → User | Who made the change |
| changed_at* | TIMESTAMP | When |

**DB indexes:** `entity_type + entity_id` (for per-entity history queries), `changed_by`, `changed_at`, `entity_type + changed_at` (for date-range queries)

**NEVER add UPDATE or DELETE operations to this table.**

---

## Entities Referenced from Other Modules

### User (owned by Module 01)
Used for `changed_by` — the user who made the change.

Fields used: `id`, `name`

### All tracked entities
AuditLog references entity IDs from Assignment, Milestone, Invoice, Project, Resource, NonHumanCost but does not have FK constraints (to allow immutable historical records even after soft-delete of the source entity).
