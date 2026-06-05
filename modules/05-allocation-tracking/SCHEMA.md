# Module 05: Allocation Tracking — Schema

## Entities Owned by This Module

### Assignment (FSD §2.7)

Full definition in `shared/ENTITIES.md §2.7`.

| Field | Type | Phase | Notes |
|---|---|---|---|
| id* | UUID PK | 1 | |
| project_id* | FK → Project | 1 | |
| resource_id* | FK → Resource | 1 | |
| allocation_pct* | INTEGER 1–100 | 1 | Capacity consumed by this project |
| billability_pct* | INTEGER 0–100 | 1 | Must be ≤ allocation_pct |
| is_shadow* | BOOLEAN DEFAULT false | 1 | If true, billability_pct must be 0 |
| project_designation | STRING(100) NULLABLE | 1 | Overrides resource.designation for this project |
| project_expertise | STRING(100) NULLABLE | 1 | Overrides resource.technical_expertise |
| billing_rate | DECIMAL(10,2) NULLABLE | 2 | Per-hour in project billing_currency. Null for shadow. |
| start_date* | DATE | 1 | |
| end_date | DATE NULLABLE | 1 | If set, auto-releases |
| status* | ENUM(ACTIVE, RELEASED, AUTO_RELEASED) DEFAULT ACTIVE | 1 | |
| released_at | TIMESTAMP NULLABLE | 1 | When assignment actually ended |
| created_at | TIMESTAMP AUTO | 1 | |
| updated_at | TIMESTAMP AUTO | 1 | |

**DB indexes:** `project_id`, `resource_id`, `status`, `end_date` (for auto-release job query)

**Unique constraint (soft):** Only one ACTIVE assignment per (resource_id, project_id). System blocks duplicate active; allows new after RELEASED/AUTO_RELEASED.

---

## Entities Referenced from Other Modules

### Project (owned by Module 03)
Fields used: `id`, `name`, `type`, `status`, `dm_id`, `pm_id`, `billing_currency`

### Resource (owned by Module 04)
Fields used: `id`, `name`, `designation`, `technical_expertise`, `loaded_cost_monthly` (Phase 2), `is_active`

### AuditLog (owned by Module 13)
All assignment writes insert rows into AuditLog. Fields written: `entity_type = 'Assignment'`, `entity_id`, `action`, `field_name`, `old_value`, `new_value`, `changed_by`, `changed_at`

### Alert (owned by Module 12)
Auto-release job creates alert rows for PM and DM on each release.
