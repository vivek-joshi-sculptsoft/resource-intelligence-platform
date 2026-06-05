# Module 07: Utilization Dashboards — Schema

## Entities Owned by This Module

**None.** This module owns no entities. All data is read from other modules.

---

## Entities Referenced from Other Modules

### Assignment (owned by Module 05)
Primary source for utilization and allocation calculations.

Fields used: `resource_id`, `project_id`, `allocation_pct`, `billability_pct`, `is_shadow`, `status`, `start_date`, `end_date`, `released_at`

See `shared/ENTITIES.md §2.7`.

### Resource (owned by Module 04)
Used for bench detection, availability, and cost calculations.

Fields used: `id`, `name`, `designation`, `technical_expertise`, `date_of_joining`, `loaded_cost_monthly` (Phase 2), `is_active`, `tags`

See `shared/ENTITIES.md §2.5`.

### Project (owned by Module 03)
Used for project-level aggregations and filtering.

Fields used: `id`, `name`, `client_id`, `type`, `status`, `dm_id`, `pm_id`, `billing_currency`, `contract_end_date`

See `shared/ENTITIES.md §2.6`.

### Client (owned by Module 02)
Used for client-level dashboard aggregations.

Fields used: `id`, `name`, `is_active`

See `shared/ENTITIES.md §2.4`.

### Invoice (owned by Module 09 — Phase 2)
Used for actual revenue in financial widgets.

Fields used: `project_id`, `amount_inr`, `status`, `invoice_date`

See `shared/ENTITIES.md §2.9`.

### NonHumanCost (owned by Module 06 — Phase 2)
Used for non-human cost totals in project and company dashboards.

Fields used: `project_id`, `amount_inr`, `is_recurring`, `cost_date`, `recurring_end_date`

See `shared/ENTITIES.md §2.10`.

### Milestone (owned by Module 09 — Phase 2)
Used for overdue milestone count in company dashboard.

Fields used: `project_id`, `planned_delivery_date`, `status`

See `shared/ENTITIES.md §2.8`.
