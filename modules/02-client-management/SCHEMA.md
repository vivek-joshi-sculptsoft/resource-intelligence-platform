# Module 02: Client Management — Schema

## Entities Owned by This Module

### Client (FSD §2.4)

Full definition in `shared/ENTITIES.md §2.4`.

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| name* | STRING(255) UNIQUE | |
| industry | STRING(100) | |
| contact_name | STRING(255) | Primary point of contact |
| contact_email | STRING(255) | |
| contact_phone | STRING(20) | |
| engagement_start_date | DATE | |
| notes | TEXT | |
| is_active | BOOLEAN DEFAULT true | Soft delete |
| created_at | TIMESTAMP AUTO | |

---

## Entities Referenced from Other Modules

### Project (owned by Module 03)

This module reads project data to show the client's project list and count active projects.

Fields used:
- `id`, `name`, `type`, `status`, `dm_id`, `pm_id`

See `shared/ENTITIES.md §2.6` for full definition.

### Assignment (owned by Module 05)

Used to count distinct active resources deployed on the client's projects.

Fields used:
- `project_id`, `resource_id`, `status` (ACTIVE only)

See `shared/ENTITIES.md §2.7` for full definition.
