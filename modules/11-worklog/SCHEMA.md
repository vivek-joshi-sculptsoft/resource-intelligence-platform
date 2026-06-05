# Module 11: Worklog — Schema

## Entities Owned by This Module

### Worklog (FSD §2.11)

Full definition in `shared/ENTITIES.md §2.11`.

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| resource_id* | FK → Resource | |
| project_id* | FK → Project | Must have active assignment AND worklog_enabled |
| log_date* | DATE | Cannot be in the future |
| hours* | DECIMAL(4,1) | 0.5–24.0; half-hour increments |
| note | TEXT NULLABLE | Optional description |
| created_at | TIMESTAMP AUTO | |

> **Decoupled by Design:** No FK or trigger relationship with Invoice, Assignment billability, or any financial entity.

**DB indexes:** `resource_id`, `project_id`, `log_date`

**Unique constraint:** (resource_id, project_id, log_date) — one entry per resource per project per day.

---

## Entities Referenced from Other Modules

### Resource (owned by Module 04)
Fields used: `id`, `name`, `is_active`

### Project (owned by Module 03)
Fields used: `id`, `name`, `worklog_enabled`, `pm_id`, `dm_id`

### Assignment (owned by Module 05)
Used to validate that the resource has (or had, for backfill) an ACTIVE assignment on the given project and log_date.

Fields used: `resource_id`, `project_id`, `status`, `start_date`, `end_date`
