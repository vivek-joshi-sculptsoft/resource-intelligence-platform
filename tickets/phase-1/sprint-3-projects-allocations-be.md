# Sprint 3 — Projects & Allocations Backend

**Goal:** Project CRUD with status lifecycle. Assignment CRUD with 7 validations. Auto-release scheduled job running.
**Capacity:** 30 SP | **Duration:** 1 week
**Epics:** EP-4 (Project Management) + EP-5 (Allocation Tracking — backend)

---

## EP-4: Project Management — Backend (14 SP)

### S3-01: Project database schema and migration
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S2-09 (clients table), S2-01 (resources table)

#### Context (read before starting)
- `modules/03-project-management/SCHEMA.md` — exact field definitions
- `shared/ENTITIES.md` → Project entity
- `CLAUDE.md` → Database conventions

#### Description
As a developer, I want the projects table so that I can build project management features.

#### Acceptance Criteria
- [ ] Alembic migration creates `projects` table: id (UUID PK), name (STRING(255)), client_id (FK→clients NOT NULL), type (ENUM: FIXED_PRICE/TIME_AND_MATERIAL/CLIENT_ONBOARDING), billing_currency (STRING(3) DEFAULT 'INR'), contract_value (DECIMAL(15,2) NULLABLE — Phase 2), start_date (DATE), contract_end_date (DATE), dm_id (FK→resources NOT NULL), pm_id (FK→resources NOT NULL), worklog_enabled (BOOLEAN DEFAULT false), notes (TEXT), status (ENUM: ACTIVE/COMPLETED/ON_HOLD/CANCELLED DEFAULT 'ACTIVE'), created_at (TIMESTAMP)
- [ ] Indexes on: client_id, dm_id, pm_id, status
- [ ] SQLAlchemy model in `app/modules/projects/models.py`
- [ ] Relationships: client, dm (Resource), pm (Resource)
- [ ] Migration reversible

---

### S3-02: Project CRUD API endpoints
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-01, S1-03

#### Context (read before starting)
- `modules/03-project-management/API.md` — all endpoints
- `modules/03-project-management/SCHEMA.md` — field definitions

#### Description
As a CEO/CTO/DM, I want to create and manage projects linked to clients and assigned managers.

#### Acceptance Criteria
- [ ] `GET /api/v1/projects` — paginated list with ?page, ?limit, ?status, ?client_id, ?type, ?dm_id, ?search
- [ ] Each list item includes: client_name, dm_name, pm_name (resolved from FKs)
- [ ] `POST /api/v1/projects` — create with all Phase 1 fields
- [ ] `GET /api/v1/projects/:id` — detail with nested client, dm, pm objects
- [ ] `PUT /api/v1/projects/:id` — update any subset of fields
- [ ] Validation: name, client_id, type, dm_id, pm_id required
- [ ] Validation: contract_end_date required for T&M and CLIENT_ONBOARDING types
- [ ] Validation: client must be active (is_active=true)
- [ ] Validation: dm_id and pm_id must reference active resources
- [ ] `contract_value` returns null in Phase 1
- [ ] All write operations audit logged
- [ ] Pydantic schemas in `app/modules/projects/schemas.py`

---

### S3-03: Project status transitions API
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-02

#### Context (read before starting)
- `modules/03-project-management/API.md` → PUT /projects/:id/status
- `shared/BUSINESS-RULES.md` → Project status transition rules (FSD §6.4)

#### Description
As a CEO/CTO/DM, I want to transition project status so that the project lifecycle is enforced.

#### Acceptance Criteria
- [ ] `PUT /api/v1/projects/:id/status` — body: `{"status": "COMPLETED|ON_HOLD|CANCELLED|ACTIVE"}`
- [ ] Valid transitions enforced per FSD §6.4:
  - ACTIVE → COMPLETED, ON_HOLD, CANCELLED
  - ON_HOLD → ACTIVE, CANCELLED
  - COMPLETED → (terminal, no further transitions)
  - CANCELLED → (terminal, no further transitions)
- [ ] Invalid transitions return 400: `{"error": true, "message": "Cannot transition from {current} to {target}"}`
- [ ] COMPLETED/CANCELLED → auto-releases all ACTIVE assignments (status=RELEASED, released_at=now)
- [ ] ON_HOLD: no automatic assignment changes
- [ ] Auth: CEO, CTO, DM (own portfolio only)
- [ ] PM cannot transition status (403)
- [ ] Each status change audit logged

---

### S3-04: Project access control
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-02, S1-03

#### Context (read before starting)
- `shared/ACCESS-MATRIX.md` → project row for all 7 roles

#### Description
As a platform, I want project endpoints role-gated per the access matrix.

#### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL — full CRUD
- [ ] DM: EDIT OWN_PORTFOLIO — CRUD on projects where dm_id = own resource_id
- [ ] PM: VIEW OWN_PORTFOLIO — read projects where pm_id = own resource_id; limited edit (worklog_enabled, notes)
- [ ] Finance: VIEW ALL — read-only access to all projects
- [ ] HR: VIEW ALL — read-only access to all projects
- [ ] Engineer: NONE — 403 on all project endpoints
- [ ] OWN_PORTFOLIO scope applied as WHERE clause: `dm_id = :resource_id OR pm_id = :resource_id`
- [ ] DM creating a project must set dm_id to self (enforced server-side)

---

### S3-05: Project module integration tests
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-01 through S3-04

#### Context (read before starting)
- `modules/03-project-management/API.md` → all endpoints
- `CLAUDE.md` → Testing Expectations

#### Description
As a developer, I want project tests so that CRUD, status transitions, and access control are proven.

#### Acceptance Criteria
- [ ] CRUD happy paths: create, read, list, update
- [ ] Validation: missing required fields → 422
- [ ] Validation: contract_end_date required for T&M → 422
- [ ] Validation: inactive client → 400
- [ ] Status transitions: all valid transitions succeed
- [ ] Status transitions: COMPLETED→ACTIVE blocked (400)
- [ ] Status transitions: CANCELLED→anything blocked (400)
- [ ] COMPLETED cascade: all ACTIVE assignments released
- [ ] Access control: DM sees only own portfolio, PM sees only own
- [ ] Access control: Engineer gets 403
- [ ] DM creating project: dm_id forced to self
- [ ] PM cannot create or transition status (403)
- [ ] Audit entries for all writes
- [ ] List filters: status, client_id, type, dm_id

---

## EP-5: Allocation Tracking — Backend (16 SP)

### S3-06: Assignment database schema and migration
**Type:** Story | **Points:** 2 (S) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-01, S2-01

#### Context (read before starting)
- `modules/05-allocation-tracking/SCHEMA.md` — exact field definitions
- `shared/ENTITIES.md` → Assignment entity
- `CLAUDE.md` → Database conventions

#### Description
As a developer, I want the assignments table so that I can build allocation tracking.

#### Acceptance Criteria
- [ ] Alembic migration creates `assignments` table: id (UUID PK), project_id (FK→projects NOT NULL), resource_id (FK→resources NOT NULL), allocation_pct (INTEGER NOT NULL CHECK 1-100), billability_pct (INTEGER NOT NULL CHECK 0-100), is_shadow (BOOLEAN DEFAULT false), project_designation (STRING(100) NULLABLE), project_expertise (STRING(100) NULLABLE), billing_rate (DECIMAL(10,2) NULLABLE — Phase 2), start_date (DATE NOT NULL), end_date (DATE NULLABLE), status (ENUM: ACTIVE/RELEASED/AUTO_RELEASED DEFAULT 'ACTIVE'), released_at (TIMESTAMP NULLABLE), created_at (TIMESTAMP), updated_at (TIMESTAMP)
- [ ] Indexes on: project_id, resource_id, status, end_date
- [ ] Unique constraint: only one ACTIVE assignment per (resource_id, project_id) — partial unique index on status='ACTIVE'
- [ ] SQLAlchemy model in `app/modules/allocations/models.py`
- [ ] Relationships: project, resource
- [ ] Migration reversible

---

### S3-07: Assignment CRUD API with 7 validations
**Type:** Story | **Points:** 5 (L) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-06, S1-03

#### Context (read before starting)
- `modules/05-allocation-tracking/API.md` — all endpoints
- `shared/BUSINESS-RULES.md` → Assignment validation rules (FSD §11)
- `modules/05-allocation-tracking/SCHEMA.md` → field definitions

#### Description
As a PM/DM, I want to assign resources to projects with full validation so that allocations are accurate.

#### Acceptance Criteria
- [ ] `GET /api/v1/projects/:projectId/assignments` — list with ?status filter
- [ ] Each item: resource nested, effective_designation (project_designation ?? resource.designation), effective_expertise
- [ ] `POST /api/v1/projects/:projectId/assignments` — create
- [ ] `GET /api/v1/assignments/:id` — single assignment with resource + project
- [ ] `PUT /api/v1/assignments/:id` — update any subset of editable fields
- [ ] `GET /api/v1/resources/:resourceId/assignments` — assignments for a resource with ?status
- [ ] **7 validations (all enforced server-side):**
  1. allocation_pct must be 1–100
  2. billability_pct must be 0–100
  3. billability_pct cannot exceed allocation_pct
  4. Shadow resources: is_shadow=true → billability_pct must be 0
  5. end_date must be after start_date (when end_date is provided)
  6. Only one ACTIVE assignment per (resource_id, project_id)
  7. Cannot create assignment on non-ACTIVE project
- [ ] Over-allocation (total > 100%): soft warning in response `{"warnings": ["Total allocation will be 140%"]}`, does NOT block save
- [ ] All write operations audit logged (one row per field)
- [ ] Pydantic schemas in `app/modules/allocations/schemas.py`

#### Out of Scope
- billing_rate (Phase 2)
- Frontend (Sprint 4)

---

### S3-08: Assignment manual release endpoint
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07

#### Context (read before starting)
- `modules/05-allocation-tracking/API.md` → POST /assignments/:id/release

#### Description
As a PM/DM, I want to manually release an assignment before its end date.

#### Acceptance Criteria
- [ ] `POST /api/v1/assignments/:id/release`
- [ ] Sets status=RELEASED, released_at=now()
- [ ] Only ACTIVE assignments can be released (400 otherwise)
- [ ] Auth: CEO, CTO, DM (own portfolio), PM (own portfolio)
- [ ] Logs "early release" if released_at < end_date in audit metadata
- [ ] Audit logged: status change + released_at change

---

### S3-09: Assignment access control and field restrictions
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07, S1-03

#### Context (read before starting)
- `shared/ACCESS-MATRIX.md` → allocation row for all 7 roles

#### Description
As a platform, I want assignment endpoints role-gated with field-level restrictions.

#### Acceptance Criteria
- [ ] CEO, CTO: EDIT ALL — full CRUD
- [ ] DM: EDIT OWN_PORTFOLIO — CRUD on assignments for projects where dm_id = self
- [ ] PM: EDIT OWN_PORTFOLIO — CRUD on assignments for projects where pm_id = self
- [ ] Finance: VIEW ALL — read-only, billing_rate visible
- [ ] HR: VIEW ALL — billability_pct, is_shadow, billing_rate returned as null
- [ ] Engineer: VIEW SELF_ONLY — own assignments only, billability_pct/is_shadow/billing_rate null
- [ ] Scope filtering via WHERE clause
- [ ] Field nulling in response serializer

---

### S3-10: Auto-release scheduled job (Celery)
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07, S0-08

#### Context (read before starting)
- `modules/05-allocation-tracking/JOBS.md` — full job spec with pseudocode
- `shared/BUSINESS-RULES.md` → Auto-release algorithm (FSD §8)
- `CLAUDE.md` → Scheduled Jobs table

#### Description
As a system, I want expired assignments auto-released daily so that utilization stays accurate.

#### Acceptance Criteria
- [ ] Celery task `auto_release_assignments` in `app/modules/allocations/jobs.py`
- [ ] Registered in celery-beat: cron `0 0 * * *` timezone Asia/Kolkata
- [ ] Query: `WHERE status = 'ACTIVE' AND end_date IS NOT NULL AND end_date <= CURRENT_DATE`
- [ ] Per assignment: set status=AUTO_RELEASED, released_at = end_date + 23:59:59
- [ ] Create ASSIGNMENT_AUTO_RELEASED alert for PM user
- [ ] Create ASSIGNMENT_AUTO_RELEASED alert for DM user (skip if same as PM)
- [ ] Audit log: 2 rows per release (status change + released_at change), changed_by='SYSTEM'
- [ ] Per-assignment error handling: log error, continue processing remaining
- [ ] Distributed lock to prevent concurrent runs
- [ ] Manual trigger endpoint: `POST /api/v1/jobs/auto-release` (admin only)
- [ ] Returns `{"released_count": N, "assignments": [...]}`

---

### S3-11: Allocation module integration tests
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-06 through S3-10

#### Context (read before starting)
- `modules/05-allocation-tracking/JOBS.md` → Testing checklist
- `modules/05-allocation-tracking/API.md` → all endpoints
- `CLAUDE.md` → Testing Expectations

#### Description
As a developer, I want comprehensive allocation tests covering all 7 validations, auto-release, and access control.

#### Acceptance Criteria
- [ ] **Validation tests (7 rules):**
  - allocation_pct < 1 → 422
  - allocation_pct > 100 → 422
  - billability_pct > allocation_pct → 422
  - is_shadow=true + billability_pct > 0 → 422
  - end_date before start_date → 422
  - Duplicate ACTIVE assignment for same resource+project → 409
  - Assignment on non-ACTIVE project → 400
- [ ] Over-allocation: 120% total → succeeds with warning in response
- [ ] **Manual release tests:**
  - Release active → RELEASED + released_at
  - Release non-active → 400
- [ ] **Auto-release job tests:**
  - end_date=yesterday → auto-released
  - end_date=today → auto-released
  - end_date=tomorrow → NOT released
  - end_date=null → NOT released
  - Already RELEASED → NOT processed
  - PM+DM same user → 1 alert (not 2)
  - PM+DM different → 2 alerts
  - Partial failure → remaining processed
  - Idempotent re-run → no duplicates
- [ ] **Access control tests:**
  - PM can create on own project
  - PM cannot create on other's project → 403
  - Engineer sees only own assignments
  - HR sees assignments but billability_pct/is_shadow = null
- [ ] Audit entries for create, update, release

---

## Sprint 3 Summary

| Story | Title | SP | Epic | Labels | Priority |
|-------|-------|---|------|--------|----------|
| S3-01 | Project schema + migration | 2 | EP-4 | database, backend | P0 |
| S3-02 | Project CRUD API | 3 | EP-4 | backend | P0 |
| S3-03 | Project status transitions | 3 | EP-4 | backend | P0 |
| S3-04 | Project access control | 2 | EP-4 | backend | P1 |
| S3-05 | Project integration tests | 3 | EP-4 | testing | P1 |
| S3-06 | Assignment schema + migration | 2 | EP-5 | database, backend | P0 |
| S3-07 | Assignment CRUD + 7 validations | 5 | EP-5 | backend | P0 |
| S3-08 | Manual release endpoint | 2 | EP-5 | backend | P1 |
| S3-09 | Assignment access control | 2 | EP-5 | backend | P1 |
| S3-10 | Auto-release job (Celery) | 3 | EP-5 | backend | P0 |
| S3-11 | Allocation integration tests | 3 | EP-5 | testing | P1 |
| **Total** | | **30** | | | |
