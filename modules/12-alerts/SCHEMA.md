# Module 12: Alerts — Schema

## Entities Owned by This Module

### Alert (FSD §2.13)

Full definition in `shared/ENTITIES.md §2.13`.

| Field | Type | Notes |
|---|---|---|
| id* | UUID PK | |
| type* | STRING(50) | CONTRACT_EXPIRY, BENCH_DURATION, OVER_ALLOCATION, MILESTONE_OVERDUE, UTILIZATION_DROP, ASSIGNMENT_AUTO_RELEASED |
| severity* | ENUM(INFO, WARNING, CRITICAL) DEFAULT INFO | |
| title* | STRING(255) | Short summary |
| message* | TEXT | Detailed content |
| recipient_user_id* | FK → User | One row per recipient per event |
| entity_type | STRING(50) NULLABLE | For deep-linking: "Project", "Resource", "Assignment", "Milestone" |
| entity_id | UUID NULLABLE | ID of the referenced entity |
| is_read | BOOLEAN DEFAULT false | |
| is_dismissed | BOOLEAN DEFAULT false | |
| created_at* | TIMESTAMP AUTO | |

**DB indexes:** `recipient_user_id`, `type`, `is_read`, `is_dismissed`, `created_at`

---

### SystemConfig (FSD §2.14)

Full definition in `shared/ENTITIES.md §2.14`. Partially seeded in Phase 1 (Module 01); full set managed here.

| Key | Type | Default |
|---|---|---|
| alert.contract_expiry_days | INTEGER | 30 |
| alert.contract_expiry_urgent_days | INTEGER | 7 |
| alert.bench_threshold_days | INTEGER | 7 |
| alert.utilization_threshold_pct | INTEGER | 70 |
| system.working_days_per_month | INTEGER | 22 |
| system.working_hours_per_day | INTEGER | 8 |
| system.default_currency | STRING | INR |

Database schema:
```
| key* | STRING(100) PK |
| value* | STRING(500) |
| description | STRING(500) |
| updated_at | TIMESTAMP AUTO |
```

---

## Entities Referenced from Other Modules

### User (owned by Module 01)
Used for `recipient_user_id`. Recipients determined by role.

### Project (owned by Module 03)
Contract expiry and milestone overdue alerts reference project entity.

### Resource (owned by Module 04)
Bench duration alerts reference resource entity.

### Assignment (owned by Module 05)
Over-allocation and auto-release alerts triggered on assignment changes.

### Milestone (owned by Module 09)
Milestone overdue alerts reference milestone entity.
