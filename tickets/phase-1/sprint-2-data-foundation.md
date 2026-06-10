# Sprint 2 — Data Foundation (Resources + Clients)

**Goal:** Resource and Client CRUD fully operational with access control, audit logging, and polished UI.
**Capacity:** 34 SP | **Duration:** 1 week
**Epics:** EP-2 (Resource Management) + EP-3 (Client Management)

---

## EP-2: Resource Management (19 SP)

### S2-01: Resource database schema and migration
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-05

#### Context (read before starting)
- `modules/04-resource-management/SCHEMA.md` — exact field definitions
- `shared/ENTITIES.md` → Resource, ResourceTag entities
- `CLAUDE.md` → Database conventions

#### Description
As a developer, I want the resource tables so that I can build resource management features.

#### Acceptance Criteria
- [ ] Alembic migration creates `resources` table: id (UUID PK), employee_id (STRING(50) UNIQUE), name (STRING(255)), designation (STRING(100)), technical_expertise (STRING(100) NULLABLE), date_of_joining (DATE), reporting_manager_id (FK→resources NULLABLE self-ref), loaded_cost_monthly (DECIMAL(15,2) NULLABLE), is_active (BOOLEAN DEFAULT true), created_at (TIMESTAMP)
- [ ] Migration creates `resource_tags` table: resource_id (FK→resources) + tag (STRING(100)) as composite PK
- [ ] Indexes on: employee_id, is_active, designation, reporting_manager_id, tag
- [ ] SQLAlchemy models in `app/modules/resources/models.py`
- [ ] Resource model has `tags` relationship (one-to-many)
- [ ] Self-referencing FK for reporting_manager_id with ON DELETE SET NULL
- [ ] Migration reversible

---

### S2-02: Resource CRUD API endpoints
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-01, S1-03

#### Context (read before starting)
- `modules/04-resource-management/API.md` — all endpoints
- `modules/04-resource-management/SCHEMA.md` — field definitions
- `shared/BUSINESS-RULES.md` → Resource-related rules

#### Description
As a CEO/CTO/HR, I want to create, view, update, and deactivate resources.

#### Acceptance Criteria
- [ ] `GET /api/v1/resources` — paginated list with ?page, ?limit, ?status, ?designation, ?expertise, ?tag, ?availability (bench/partial/full), ?search
- [ ] Each list item includes computed `total_allocation_pct` (sum of active assignment allocation_pct)
- [ ] `POST /api/v1/resources` — create with all Phase 1 fields + tags array
- [ ] `GET /api/v1/resources/:id` — full profile with active_assignments, total_allocation_pct, reporting_manager nested
- [ ] `PUT /api/v1/resources/:id` — update any subset of fields
- [ ] `DELETE /api/v1/resources/:id` — soft-deactivate (is_active=false)
- [ ] Validation: name, employee_id, designation required
- [ ] Validation: employee_id unique (409 Conflict on duplicate)
- [ ] Validation: cannot self-reference as reporting_manager
- [ ] Deactivation blocked if resource is DM or PM on an ACTIVE project
- [ ] Deactivation cascades: releases all ACTIVE assignments
- [ ] All write operations audit logged
- [ ] Pydantic request/response schemas in `app/modules/resources/schemas.py`

---

### S2-03: Resource access control and field restrictions
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-02, S1-03

#### Context (read before starting)
- `shared/ACCESS-MATRIX.md` → resource_profiles row for all 7 roles
- `CLAUDE.md` → Access Control Implementation

#### Description
As a platform, I want resource endpoints role-gated so that sensitive data stays restricted.

#### Acceptance Criteria
- [ ] CEO, CTO, HR: EDIT ALL — full CRUD
- [ ] DM, PM: VIEW OWN_PORTFOLIO — read resources on their projects
- [ ] Finance: VIEW ALL — can read all, no edit (except loaded_cost_monthly in Phase 2)
- [ ] Engineer: VIEW SELF_ONLY — sees only own resource record
- [ ] `loaded_cost_monthly` returned as `null` for DM, PM, HR, Engineer
- [ ] `billing_rate`, `billability_pct`, `is_shadow` on assignments returned as `null` for HR, Engineer
- [ ] Scope filtering via WHERE clause (not post-fetch)
- [ ] 403 for unauthorized access attempts

---

### S2-04: Resource tag management endpoints
**Type:** Story | **Points:** 1 (XS) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-02

#### Context (read before starting)
- `modules/04-resource-management/API.md` → POST/DELETE tag endpoints

#### Description
As a CEO/CTO/HR/DM, I want to add and remove resource tags for skill categorization.

#### Acceptance Criteria
- [ ] `POST /api/v1/resources/:id/tags` — body: `{"tag": "string"}` — returns updated tags array
- [ ] `DELETE /api/v1/resources/:id/tags/:tag` — returns updated tags array
- [ ] Tag max 100 chars validation
- [ ] Duplicate tag: 409 or no-op (idempotent)
- [ ] Auth: CEO, CTO, HR (all resources); DM (own portfolio only)
- [ ] Audit logged

---

### S2-05: Resource List screen UI
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-02, S1-06

#### Context (read before starting)
- `modules/04-resource-management/SCREENS.md` → Resource List spec
- `shared/ACCESS-MATRIX.md` → role visibility for resource data

#### Description
As a manager, I want a resource list page so that I can see all team members and their availability.

#### Acceptance Criteria
- [ ] `/resources` route — full-width data table
- [ ] Columns: Name (link), Employee ID, Designation, Expertise, Tags (pill badges), Total Allocation %, Availability badge (Bench/Partial/Full), Status badge
- [ ] Search input: by name or employee ID
- [ ] Filters: designation dropdown, expertise dropdown, tags multi-select, availability (Bench/Partial/Full/All)
- [ ] Status filter: Active / Inactive / All
- [ ] Column sorting on all columns
- [ ] Pagination with page size selector
- [ ] "Add Resource" button — visible to CEO, CTO, HR only
- [ ] Click row → `/resources/:id`
- [ ] Allocation % highlighted red when > 100%
- [ ] Empty state: "No resources found. Try adjusting filters."
- [ ] Engineer sees only own record (API enforces, but UI hides "Add" button and filters)

---

### S2-06: Resource Profile screen UI
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-02, S2-05

#### Context (read before starting)
- `modules/04-resource-management/SCREENS.md` → Resource Profile spec
- `shared/ACCESS-MATRIX.md` → field-level restrictions per role

#### Description
As a manager, I want a resource profile page so that I can see a resource's full details and assignments.

#### Acceptance Criteria
- [ ] `/resources/:id` route — header + stats row + tabs
- [ ] Header: name, employee ID, designation, expertise, date of joining, reporting manager (link), tags (editable inline), edit button
- [ ] Stats row: total allocation %, availability status badge, days on bench (if 0% allocated)
- [ ] Active Assignments tab: table with project name (link), project designation, allocation %, start/end date, status
- [ ] Assignment History tab: same columns, showing RELEASED/AUTO_RELEASED
- [ ] Edit button → `/resources/:id/edit` (CEO/CTO/HR only)
- [ ] `loaded_cost_monthly` hidden (Phase 2)
- [ ] `billing_rate`, `billability_pct`, `is_shadow` hidden for HR/Engineer per access matrix
- [ ] Assignments empty state: "No active assignments. This resource is on bench."

---

### S2-07: Resource Create/Edit form UI
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-02, S2-05

#### Context (read before starting)
- `modules/04-resource-management/SCREENS.md` → Resource Create/Edit Form spec

#### Description
As a CEO/CTO/HR, I want a resource form so that I can add and edit team members.

#### Acceptance Criteria
- [ ] `/resources/new` and `/resources/:id/edit` routes
- [ ] Fields: Name (required), Employee ID (required), Designation (required), Technical Expertise, Date of Joining (date picker), Reporting Manager (dropdown from active resources), Tags (tag input with add/remove)
- [ ] Edit form pre-populates all fields from API
- [ ] Client-side validations: required fields, employee_id format
- [ ] Server error display: "Employee ID is already in use" on 409
- [ ] Save → redirect to resource profile with success toast
- [ ] Cancel → back to resource list
- [ ] `loaded_cost_monthly` field hidden (Phase 2)
- [ ] Only accessible to CEO, CTO, HR

---

### S2-08: Resource module integration tests
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-01 through S2-04

#### Context (read before starting)
- `modules/04-resource-management/API.md` → all endpoints
- `CLAUDE.md` → Testing Expectations

#### Description
As a developer, I want resource tests so that CRUD, access control, and edge cases are covered.

#### Acceptance Criteria
- [ ] CRUD happy paths: create, read, list, update, deactivate
- [ ] employee_id uniqueness enforced (409)
- [ ] Self-referencing reporting manager blocked
- [ ] Deactivation with active DM/PM assignment blocked
- [ ] Deactivation cascades: releases active assignments
- [ ] Tag add/remove happy path
- [ ] Access control: HR can create, PM cannot (403)
- [ ] Scope: Engineer sees only own resource
- [ ] Field restriction: loaded_cost_monthly null for PM role
- [ ] List filters: availability=bench, designation, tag
- [ ] Audit log entries created for all writes
- [ ] Pagination works correctly

---

## EP-3: Client Management (15 SP)

### S2-09: Client database schema and migration
**Type:** Story | **Points:** 1 (XS) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S0-05

#### Context (read before starting)
- `modules/02-client-management/SCHEMA.md` — exact field definitions
- `shared/ENTITIES.md` → Client entity

#### Description
As a developer, I want the client table so that I can build client management features.

#### Acceptance Criteria
- [ ] Alembic migration creates `clients` table: id (UUID PK), name (STRING(255) UNIQUE), industry (STRING(100)), contact_name (STRING(255)), contact_email (STRING(255)), contact_phone (STRING(20)), engagement_start_date (DATE), notes (TEXT), is_active (BOOLEAN DEFAULT true), created_at (TIMESTAMP)
- [ ] Index on is_active, name
- [ ] SQLAlchemy model in `app/modules/clients/models.py`
- [ ] Migration reversible

---

### S2-10: Client CRUD API endpoints
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-09, S1-03

#### Context (read before starting)
- `modules/02-client-management/API.md` — all endpoints
- `modules/02-client-management/SCHEMA.md` — field definitions

#### Description
As a CEO/CTO, I want to manage clients so that project relationships are tracked.

#### Acceptance Criteria
- [ ] `GET /api/v1/clients` — paginated list with ?page, ?limit, ?status, ?search
- [ ] Each list item includes computed `active_project_count`
- [ ] `POST /api/v1/clients` — create with all fields
- [ ] `GET /api/v1/clients/:id` — detail with projects list and dashboard stats (active_resource_count, active_project_count, project_count_by_type)
- [ ] `PUT /api/v1/clients/:id` — update any subset
- [ ] `DELETE /api/v1/clients/:id` — soft-deactivate
- [ ] Validation: name required, name unique (409 on duplicate)
- [ ] Deactivation blocked if active projects exist for this client
- [ ] Financial dashboard fields (total_monthly_billing_inr, total_cost_inr, aggregate_margin_inr) return `null` in Phase 1
- [ ] All write operations audit logged
- [ ] Pydantic schemas in `app/modules/clients/schemas.py`

---

### S2-11: Client access control
**Type:** Story | **Points:** 1 (XS) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-10, S1-03

#### Context (read before starting)
- `shared/ACCESS-MATRIX.md` → client row for all 7 roles

#### Description
As a platform, I want client endpoints role-gated per the access matrix.

#### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL — full CRUD
- [ ] DM, PM: VIEW OWN_PORTFOLIO — see only clients with projects they manage
- [ ] Finance, HR: VIEW ALL — read all, no create/edit
- [ ] Engineer: NONE — 403 on all client endpoints
- [ ] Scope filtering via WHERE clause
- [ ] OWN_PORTFOLIO: filters by clients that have projects where dm_id or pm_id = user.resource_id

---

### S2-12: Client List screen UI
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-10, S1-06

#### Context (read before starting)
- `modules/02-client-management/SCREENS.md` → Client List spec

#### Description
As a manager, I want a client list page so that I can see all client relationships.

#### Acceptance Criteria
- [ ] `/clients` route — full-width data table
- [ ] Columns: Name (link), Industry, Engagement Start Date, Active Projects (count), Status badge
- [ ] "Add Client" button — CEO, CTO only
- [ ] Status filter: Active / Inactive / All
- [ ] Search input by client name
- [ ] Column sorting on name, engagement_start_date
- [ ] Click row → `/clients/:id`
- [ ] Empty state: "No clients found. Add your first client to get started."
- [ ] Not visible to Engineer role (sidebar nav hides link)

---

### S2-13: Client Detail screen UI
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-10, S2-12

#### Context (read before starting)
- `modules/02-client-management/SCREENS.md` → Client Detail spec

#### Description
As a manager, I want a client detail page so that I can see client info and their projects.

#### Acceptance Criteria
- [ ] `/clients/:id` route — header + stats row + projects table
- [ ] Header: name, industry, contact name/email/phone, engagement start, notes, edit button (CEO/CTO)
- [ ] Stats row: active resource count, active project count
- [ ] Financial stats hidden in Phase 1 (will show null placeholders in Phase 2)
- [ ] Projects table: name (link), type badge, status badge, DM name, PM name
- [ ] Click project → `/projects/:id`
- [ ] Deactivate button (CEO/CTO) with confirmation dialog
- [ ] Deactivation blocked message if active projects exist
- [ ] Projects empty state: "No projects yet. Add a project for this client."

---

### S2-14: Client Create/Edit form UI
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-10, S2-12

#### Context (read before starting)
- `modules/02-client-management/SCREENS.md` → Client Create/Edit Form spec

#### Description
As a CEO/CTO, I want a client form so that I can add and edit client records.

#### Acceptance Criteria
- [ ] `/clients/new` and `/clients/:id/edit` routes
- [ ] Fields: Name (required), Industry, Contact Name, Contact Email, Contact Phone, Engagement Start Date (date picker), Notes (textarea)
- [ ] Edit form pre-populates all fields
- [ ] Client-side validations: name required, email format
- [ ] Server error display: "Client name already exists" on 409
- [ ] Save → redirect to client detail with success toast
- [ ] Cancel → back to client list
- [ ] Only accessible to CEO, CTO

---

### S2-15: Client module integration tests
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-09 through S2-11

#### Context (read before starting)
- `modules/02-client-management/API.md` → all endpoints
- `CLAUDE.md` → Testing Expectations

#### Description
As a developer, I want client tests so that CRUD, access control, and edge cases are covered.

#### Acceptance Criteria
- [ ] CRUD happy paths: create, read, list, update, deactivate
- [ ] Name uniqueness enforced (409)
- [ ] Deactivation with active projects blocked
- [ ] Access control: CEO/CTO can create, DM/PM cannot (403)
- [ ] Engineer gets 403 on all endpoints
- [ ] OWN_PORTFOLIO scope: DM sees only clients with their projects
- [ ] Dashboard endpoint returns active counts
- [ ] Financial fields return null in Phase 1
- [ ] Audit log entries for all writes
- [ ] Pagination and search work correctly

---

## Sprint 2 Summary

| Story | Title | SP | Epic | Labels | Priority |
|-------|-------|---|------|--------|----------|
| S2-01 | Resource schema + migration | 2 | EP-2 | database, backend | P0 |
| S2-02 | Resource CRUD API | 3 | EP-2 | backend | P0 |
| S2-03 | Resource access control | 2 | EP-2 | backend | P0 |
| S2-04 | Resource tag endpoints | 1 | EP-2 | backend | P1 |
| S2-05 | Resource List UI | 3 | EP-2 | frontend | P1 |
| S2-06 | Resource Profile UI | 3 | EP-2 | frontend | P1 |
| S2-07 | Resource Create/Edit form | 3 | EP-2 | frontend | P1 |
| S2-08 | Resource integration tests | 2 | EP-2 | testing | P1 |
| S2-09 | Client schema + migration | 1 | EP-3 | database, backend | P0 |
| S2-10 | Client CRUD API | 3 | EP-3 | backend | P0 |
| S2-11 | Client access control | 1 | EP-3 | backend | P1 |
| S2-12 | Client List UI | 2 | EP-3 | frontend | P1 |
| S2-13 | Client Detail UI | 3 | EP-3 | frontend | P1 |
| S2-14 | Client Create/Edit form | 2 | EP-3 | frontend | P1 |
| S2-15 | Client integration tests | 2 | EP-3 | testing | P1 |
| **Total** | | **33** | | | |
