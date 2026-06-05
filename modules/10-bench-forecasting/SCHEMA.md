# Module 10: Bench & Availability Forecasting — Schema

## Entities Owned by This Module

**None.** This module reads from existing entities only.

---

## Entities Referenced from Other Modules

### Assignment (owned by Module 05)

Primary source. Bench = resource with 0 ACTIVE assignments. Upcoming releases = ACTIVE assignments with end_date within window.

Fields used: `resource_id`, `project_id`, `allocation_pct`, `status`, `end_date`, `released_at`

See `shared/ENTITIES.md §2.7`.

### Resource (owned by Module 04)

Used for profile info, bench start calculation, and bench cost.

Fields used: `id`, `name`, `designation`, `technical_expertise`, `date_of_joining`, `loaded_cost_monthly` (Phase 2), `is_active`, `tags`

See `shared/ENTITIES.md §2.5`.

### Project (owned by Module 03)

Used to show project names alongside availability data.

Fields used: `id`, `name`, `client_id`

See `shared/ENTITIES.md §2.6`.
