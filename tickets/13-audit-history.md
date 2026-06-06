# Module 13: Audit History -- JIRA Tickets

---

## Story: Create AuditLog database table
**Type:** Task
**Phase:** 1
**Module:** 13-audit-history
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles
**Labels:** backend, database

### Description
Create the database migration for the AuditLog table per SCHEMA.md. Uses BIGINT auto-increment PK (not UUID) for high-insert performance. The table is append-only -- no UPDATE or DELETE operations are ever allowed. Add composite indexes for per-entity history queries and date-range queries. No foreign key constraint on entity_id to allow immutable records even after source entity soft-delete.

### Acceptance Criteria
- [ ] AuditLog table created: id (BIGINT PK auto-increment), entity_type (STRING(50)), entity_id (UUID), action (ENUM: CREATE/UPDATE/DELETE), field_name (STRING(100) NULLABLE), old_value (TEXT NULLABLE), new_value (TEXT NULLABLE), changed_by (FK -> User), changed_at (TIMESTAMP)
- [ ] DB indexes: (entity_type, entity_id), changed_by, changed_at, (entity_type, changed_at)
- [ ] No FK constraint on entity_id (allows historical records after soft-delete)
- [ ] No UPDATE or DELETE permissions granted on this table at database level
- [ ] Migration is idempotent

---

## Story: Build audit logging wrapper function
**Type:** Feature
**Phase:** 1
**Module:** 13-audit-history
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 13-audit-history (DB table)
**Labels:** backend

### Description
Build the shared audit logging wrapper that all modules must use for write operations. The wrapper accepts entity_type, entity_id, action (CREATE/UPDATE/DELETE), an array of field changes, changed_by (user_id), and changed_at (defaults to now). For CREATE: one row per field with old_value = null. For UPDATE: one row per changed field with both old and new values. For DELETE: one row with old_value = last known state. Values are JSON-serialized strings. The wrapper must never throw errors that block the primary operation.

### Acceptance Criteria
- [ ] auditLog() function signature: entity_type, entity_id, action, changes[], changed_by, changed_at
- [ ] CREATE: inserts one row per field with old_value = null, new_value = JSON-serialized value
- [ ] UPDATE: inserts one row per changed field with old_value and new_value as JSON strings
- [ ] DELETE: inserts one row with field_name = null, old_value = serialized entity state
- [ ] changed_at defaults to now() if not provided
- [ ] Wrapper handles errors gracefully (logs failure but does not block primary operation)
- [ ] Wrapper is importable and usable by all modules
- [ ] Unit tests for CREATE, UPDATE, DELETE operations with various field types
- [ ] Unit tests verifying one row per changed field (not one row per save)

---

## Story: Integrate audit logging into Module 01 (Auth & Roles)
**Type:** Task
**Phase:** 1
**Module:** 13-audit-history
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 13-audit-history (audit wrapper), 01-auth-and-roles
**Labels:** backend

### Description
Wrap all CREATE/UPDATE/DELETE operations in Module 01 (User, Role, RolePermission) with the audit logging wrapper. Ensure every write operation generates appropriate audit log entries.

### Acceptance Criteria
- [ ] User create/update/deactivation generates audit log entries
- [ ] Role changes generate audit log entries
- [ ] RolePermission changes generate audit log entries
- [ ] One row per changed field for updates
- [ ] Integration tests verifying audit entries are created

---

## Story: Integrate audit logging into Modules 02-05
**Type:** Task
**Phase:** 1
**Module:** 13-audit-history
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 13-audit-history (audit wrapper), 02-client-management, 03-project-management, 04-resource-management, 05-allocation-tracking
**Labels:** backend

### Description
Wrap all CREATE/UPDATE/DELETE operations in Modules 02 (Client), 03 (Project), 04 (Resource), and 05 (Assignment) with the audit logging wrapper. Focus on tracked fields per FSD Section 13: Assignment (ALL fields), Project (status, contract_end_date, contract_value), Resource (designation, loaded_cost_monthly, is_active).

### Acceptance Criteria
- [ ] Client create/update/deactivation generates audit log entries
- [ ] Project status, contract_end_date, contract_value changes are audit logged
- [ ] Resource designation, loaded_cost_monthly, is_active changes are audit logged
- [ ] Assignment ALL fields tracked: allocation_pct, billability_pct, is_shadow, billing_rate, project_designation, project_expertise, start_date, end_date, status
- [ ] One row per changed field for updates
- [ ] Auto-release (status change to AUTO_RELEASED) generates audit entries
- [ ] Integration tests verifying audit entries for each tracked entity and field

---

## Story: Integrate audit logging into Modules 06, 08, 09
**Type:** Task
**Phase:** 2
**Module:** 13-audit-history
**Priority:** P0
**Estimate:** M (3-5d)
**Depends On:** 13-audit-history (audit wrapper), 06-non-human-costs, 08-financial-engine, 09-invoicing
**Labels:** backend

### Description
Wrap all CREATE/UPDATE/DELETE operations in Phase 2 modules with the audit logging wrapper. Tracked fields per FSD Section 13: NonHumanCost (ALL fields), Milestone (status, planned_delivery_date, actual_delivery_date, amount), Invoice (amount, exchange_rate, status). Also covers loaded_cost_monthly updates (Module 08) and billing_rate updates.

### Acceptance Criteria
- [ ] NonHumanCost ALL fields tracked on create/update/delete
- [ ] Milestone status, planned_delivery_date, actual_delivery_date, amount changes are audit logged
- [ ] Milestone status transitions generate audit entries
- [ ] Invoice amount, exchange_rate, status changes are audit logged
- [ ] Invoice status transitions generate audit entries
- [ ] loaded_cost_monthly changes on Resource are audit logged
- [ ] billing_rate changes on Assignment are audit logged
- [ ] Integration tests verifying audit entries for each tracked entity

---

## Story: Integrate audit logging into Module 12 (SystemConfig)
**Type:** Task
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 13-audit-history (audit wrapper), 12-alerts (SystemConfig API)
**Labels:** backend

### Description
Wrap SystemConfig updates with the audit logging wrapper. When a config key-value pair is changed, log the old and new values. This ensures admin threshold changes are fully traceable.

### Acceptance Criteria
- [ ] SystemConfig value updates generate audit log entries
- [ ] Audit entry captures: entity_type = "SystemConfig", entity_id = key, old_value, new_value
- [ ] Integration test verifying audit entry on config change

---

## Story: Build audit log viewer API (Phase 3)
**Type:** Feature
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P1
**Estimate:** M (3-5d)
**Depends On:** 13-audit-history (DB table, audit wrapper with data)
**Labels:** backend

### Description
Implement `GET /api/audit-logs` for querying audit history with filters: entity_type, entity_id, changed_by, date range. Returns paginated results with resolved entity names and user names. Scoped: CEO/CTO see ALL, DM/PM see OWN_PORTFOLIO entities only (filtered by their project assignments).

### Acceptance Criteria
- [ ] GET /api/audit-logs returns paginated audit entries
- [ ] Supports filters: ?entity_type, ?entity_id, ?changed_by, ?start_date, ?end_date, ?page, ?limit (default 50)
- [ ] Response includes resolved entity_name (display name of the entity)
- [ ] Response includes changed_by as {id, name}
- [ ] CEO, CTO see all audit entries (ALL scope)
- [ ] DM sees entries for entities within own portfolio (OWN_PORTFOLIO)
- [ ] PM sees entries for entities within own portfolio (OWN_PORTFOLIO)
- [ ] Finance, HR, Engineer: no access (403)
- [ ] Sorted by changed_at DESC
- [ ] Unit tests for filtering, pagination, and scope enforcement

---

## Story: Build entity-specific audit history API (Phase 3)
**Type:** Feature
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P1
**Estimate:** S (1-2d)
**Depends On:** 13-audit-history (audit log viewer API)
**Labels:** backend

### Description
Implement `GET /api/audit-logs/:entityType/:entityId` to return the full audit history for one specific entity record. Returns all audit rows sorted by changed_at DESC. Same access control as the main audit log viewer: CEO/CTO ALL, DM/PM OWN_PORTFOLIO.

### Acceptance Criteria
- [ ] Returns all audit rows for the given entity_type + entity_id
- [ ] Sorted by changed_at DESC
- [ ] CEO, CTO see any entity's history
- [ ] DM, PM see only entities within their portfolio
- [ ] Finance, HR, Engineer: no access
- [ ] Unit tests for query and access control

---

## Story: Build point-in-time reconstruction API (Phase 3)
**Type:** Feature
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P2
**Estimate:** L (5-10d)
**Depends On:** 13-audit-history (entity-specific audit API)
**Labels:** backend

### Description
Implement `GET /api/audit-logs/:entityType/:entityId/point-in-time?date=<ISO-date>` to reconstruct entity state as of any past date. Algorithm per FSD Section 13: get current entity state, then replay all audit entries after the target date in reverse chronological order (for each entry, set field = old_value). Restricted to CEO and CTO only.

### Acceptance Criteria
- [ ] Accepts entity_type, entity_id, and target date
- [ ] Gets current entity state from the database
- [ ] Collects all audit entries for this entity after the target date, sorted DESC
- [ ] Replays entries in reverse: for each UPDATE entry, sets field = old_value
- [ ] For DELETE entries after target date: reconstructs entity from old_value
- [ ] Returns reconstructed entity state as JSON
- [ ] Restricted to CEO and CTO only
- [ ] Handles edge cases: entity did not exist on target date, no changes after target date
- [ ] Unit tests with known state transitions and expected reconstruction results

---

## Story: Build audit log viewer UI (Phase 3)
**Type:** Feature
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P1
**Estimate:** L (5-10d)
**Depends On:** 13-audit-history (audit log viewer API)
**Labels:** frontend

### Description
Build the `/audit` page with a full-width table and filter bar. Filters: entity type dropdown, changed_by user dropdown, date range pickers, search by entity name or ID. Table shows: When, Who, Entity Type (badge), Entity (link), Action (CREATE/UPDATE/DELETE badge), Field Changed, Old Value, New Value. Sorted by changed_at DESC. CEO/CTO see all history; DM/PM see own portfolio entities.

### Acceptance Criteria
- [ ] Entity type filter: All / Assignment / Project / Resource / Milestone / Invoice / NonHumanCost
- [ ] Changed By user filter dropdown
- [ ] Date range filter (start/end date pickers)
- [ ] Search by entity name or ID
- [ ] Table columns: When (full date + time), Who, Entity Type (badge), Entity (link to detail), Action (badge), Field Changed, Old Value (formatted/truncated), New Value (formatted/truncated)
- [ ] Sorted by changed_at DESC
- [ ] Click entity name navigates to entity detail
- [ ] Pagination for large result sets
- [ ] CEO, CTO see all history
- [ ] DM, PM see only own portfolio entities
- [ ] Finance, HR, Engineer: no access (redirect or 403)
- [ ] Empty state: "No audit log entries match your filters."

---

## Story: Build change history panel for entity detail views (Phase 3)
**Type:** Feature
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P2
**Estimate:** M (3-5d)
**Depends On:** 13-audit-history (entity-specific audit API)
**Labels:** frontend

### Description
Add a "History" section or tab within entity detail views (Assignment, Project, Resource, Milestone, Invoice). Shows last 20 changes in a compact timeline format: timestamp (relative), changed by, field name, old -> new value. Includes a "View full history" link to the audit log viewer filtered for that entity. Accessible to CEO, CTO, DM, PM (own portfolio).

### Acceptance Criteria
- [ ] History section/tab added to: Assignment, Project, Resource, Milestone, Invoice detail views
- [ ] Shows last 20 changes for the entity
- [ ] Each entry: timestamp (relative, e.g., "3 days ago"), changed by (user name), field name, change (e.g., "60% -> 80%")
- [ ] "View full history" link navigates to /audit?entity_type=X&entity_id=Y
- [ ] Accessible to CEO, CTO, DM, PM (own portfolio)
- [ ] Empty state: "No changes recorded yet."

---

## Story: Build point-in-time reconstruction UI (Phase 3)
**Type:** Feature
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P3
**Estimate:** M (3-5d)
**Depends On:** 13-audit-history (point-in-time API)
**Labels:** frontend

### Description
Build the `/audit/reconstruct` admin tool page for CEO and CTO. Simple query form with Entity Type dropdown, Entity ID input, Target Date picker, and "Reconstruct" button. Results displayed as formatted JSON or a structured entity state table. Restricted to CEO and CTO only.

### Acceptance Criteria
- [ ] Entity Type dropdown (Assignment, Project, Resource, Milestone, Invoice, NonHumanCost)
- [ ] Entity ID text input
- [ ] Target Date picker
- [ ] "Reconstruct" button triggers API call
- [ ] Results displayed as formatted JSON or structured table
- [ ] Loading state during reconstruction
- [ ] Error handling: entity not found, entity did not exist on target date
- [ ] Restricted to CEO and CTO only
- [ ] Empty state: "Enter an entity type, ID, and date to reconstruct its state."

---

## Story: Implement audit history access control (Phase 3)
**Type:** Task
**Phase:** 3
**Module:** 13-audit-history
**Priority:** P0
**Estimate:** S (1-2d)
**Depends On:** 01-auth-and-roles, 13-audit-history (all Phase 3 APIs)
**Labels:** backend

### Description
Enforce access control across all audit history viewer endpoints per ACCESS-MATRIX.md. CEO and CTO have full access to all audit history. DM and PM can view audit entries for entities within their portfolio only (OWN_PORTFOLIO scope). Finance, HR, and Engineer have no access to audit viewer endpoints. Point-in-time reconstruction is CEO/CTO only. Scope filtering via WHERE clauses at database level.

### Acceptance Criteria
- [ ] CEO, CTO: VIEW ALL audit entries and point-in-time reconstruction
- [ ] DM: VIEW audit entries for entities within own portfolio (projects where dm_id = current user)
- [ ] PM: VIEW audit entries for entities within own portfolio (projects where pm_id = current user)
- [ ] Finance, HR, Engineer: no access to audit viewer endpoints (403)
- [ ] Point-in-time reconstruction: CEO and CTO only
- [ ] Scope filtering applied at DB query level (WHERE clause)
- [ ] Access control tests for all 7 roles
