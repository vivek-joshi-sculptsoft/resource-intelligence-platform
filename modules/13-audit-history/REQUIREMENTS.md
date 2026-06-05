# Module 13: Audit History

## Overview

AuditLog is the immutable append-only record of every field change across all tracked entities. This module provides the logging infrastructure (Phase 1, used by all other modules from day one) and the UI for browsing and querying audit history (Phase 3). It also supports point-in-time reconstruction: given a past date, replay the audit log to reconstruct the state of any entity.

## Phase

Phase 1 (logging infrastructure — no UI). Phase 3 adds the viewer UI and historical queries.

## Dependencies

- Module 01 (Auth & Roles)
- All other modules depend on this for audit logging

---

## Features

### Feature: Audit Logging Infrastructure (Phase 1)
**Description:** Capture every CREATE, UPDATE, DELETE across all tracked entities.
**Acceptance Criteria:**
- [ ] One audit row per changed field per operation (not one row per save)
- [ ] For CREATE: one row per field with old_value = null, new_value = serialized value
- [ ] For UPDATE: one row per changed field with old_value and new_value
- [ ] For DELETE/deactivation: one row with action = DELETE, old_value = last known value
- [ ] Captured fields: entity_type, entity_id, action, field_name, old_value, new_value, changed_by, changed_at
- [ ] AuditLog is never updated or deleted — append only
- [ ] Logging wrapped around all write operations across all modules

### Tracked Entities and Fields (FSD §13)

| Entity | Tracked Fields |
|---|---|
| Assignment | ALL (allocation_pct, billability_pct, is_shadow, billing_rate, project_designation, project_expertise, start_date, end_date, status) |
| Milestone | status, planned_delivery_date, actual_delivery_date, amount |
| Invoice | amount, exchange_rate, status |
| Project | status, contract_end_date, contract_value |
| Resource | designation, loaded_cost_monthly, is_active |
| NonHumanCost | ALL fields |

### Feature: Audit Log Viewer (Phase 3)
**Description:** Browse and search audit history.
**Acceptance Criteria:**
- [ ] Filter by: entity_type, entity_id (specific record), changed_by (user), date range
- [ ] Show: entity type, entity name, field changed, old value, new value, changed by, changed at
- [ ] Sortable by changed_at
- [ ] Accessible to CEO, CTO only (full history); DM/PM (own portfolio entities only)

### Feature: Change History Panel (Phase 3)
**Description:** Show recent changes inline within entity detail views.
**Acceptance Criteria:**
- [ ] "History" section or tab within Assignment, Project, Resource, Milestone, Invoice detail views
- [ ] Shows last N changes with field, old/new values, changed by, date

### Feature: Point-in-Time Reconstruction (Phase 3)
**Description:** Reconstruct entity state as of any past date.
**Acceptance Criteria:**
- [ ] Given entity_type + entity_id + target_date, return the entity state as it was on that date
- [ ] Algorithm: get current state, then replay all changes after target_date backwards (set field = old_value)
- [ ] Accessible to CEO, CTO only

---

## Validations

No user-facing writes. AuditLog is write-only via internal logging wrapper. No user can create, edit, or delete audit entries.

---

## Business Rules

- AuditLog is append-only — no UPDATE or DELETE on this table ever
- Log one row per changed field, not one row per save
- old_value and new_value stored as JSON-serialized strings
- Point-in-time algorithm from FSD §13 — replay log backwards
- All modules must use the shared audit logging wrapper; bypass is not allowed
