# Sprint 5 — Dashboards, Worklog & Polish

**Goal:** Company dashboard live. Resource availability view. Worklog entry for engineers. E2E smoke tests. Phase 1 complete.
**Capacity:** 37 SP | **Duration:** 1 week
**Epics:** EP-6 (Utilization Dashboards) + EP-7 (Worklog) + EP-9 (Integration Testing & Polish)

---

## EP-6: Utilization Dashboards (18 SP)

### S5-01: Company dashboard API
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07 (assignments exist), S2-02 (resources exist), S3-02 (projects exist)

#### Context (read before starting)
- `modules/07-utilization-dashboards/API.md` → GET /dashboard/company
- `shared/BUSINESS-RULES.md` → §7.1 Company Utilization formula
- `shared/ACCESS-MATRIX.md` → CEO/CTO only

#### Description
As a CEO/CTO, I want a company dashboard API so that the frontend can render KPI widgets.

#### Acceptance Criteria
- [ ] `GET /api/v1/dashboard/company` — aggregated response
- [ ] `billable_utilization_pct`: formula from BUSINESS-RULES.md §7.1 — (sum of billability_pct for ACTIVE non-shadow assignments) / (count of active resources × 100) × 100
- [ ] `total_active_resources`: count of resources with is_active=true
- [ ] `bench_count` + `bench_resources[]`: resources with 0 ACTIVE assignments, each with days_on_bench
- [ ] `shadow_count` + `shadow_total_allocation_pct`: assignments where is_shadow=true
- [ ] `active_project_count` + `active_projects_by_type`: GROUP BY type
- [ ] `upcoming_releases_30d[]`: ACTIVE assignments with end_date in next 30 days, with days_remaining
- [ ] Phase 2 financial fields return `null`
- [ ] Auth: CEO, CTO only (403 for others)
- [ ] Response < 2s for 50 resources / 30 projects (typical dataset)

---

### S5-02: DM portfolio dashboard API
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-01

#### Context (read before starting)
- `modules/07-utilization-dashboards/API.md` → GET /dashboard/dm

#### Description
As a DM, I want my portfolio dashboard API so that I see metrics scoped to my projects.

#### Acceptance Criteria
- [ ] `GET /api/v1/dashboard/dm` — scoped to projects where dm_id = current user's resource_id
- [ ] `portfolio_utilization_pct`: same formula as company but scoped to DM's resources
- [ ] `active_project_count`, `resource_count`, `bench_count` (resources on DM's projects with no other active assignment)
- [ ] `upcoming_releases_30d[]` scoped to portfolio
- [ ] Auth: DM (own portfolio), CEO, CTO
- [ ] Financial fields return `null` (Phase 2)

---

### S5-03: Resource availability API
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-07, S2-02

#### Context (read before starting)
- `modules/07-utilization-dashboards/API.md` → GET /dashboard/availability
- `modules/07-utilization-dashboards/SCREENS.md` → Resource Availability View
- `modules/07-utilization-dashboards/mockups/availability.html` → Visual mockup reference

#### Description
As any user, I want a resource availability API so that I can find who's available for projects.

#### Acceptance Criteria
- [ ] `GET /api/v1/dashboard/availability` — returns 4 sections
- [ ] `bench[]`: resources with 0 ACTIVE assignments — id, name, designation, expertise, days_on_bench, tags
- [ ] `partial[]`: resources with total_allocation < 100% — id, name, total_allocation_pct, spare_capacity_pct, project names
- [ ] `releasing_soon[]`: ACTIVE assignments with end_date in next N days — name, project, allocation_pct, end_date, days_remaining
- [ ] `fully_allocated[]`: resources with total_allocation >= 100% — name, total_allocation_pct, project names
- [ ] `?window=30|60|90` filter for releasing_soon (default 30)
- [ ] Auth: all authenticated roles including Engineer
- [ ] No financial data exposed (billing_rate, billability, shadow status, CTC excluded)

---

### S5-04: Company Dashboard UI
**Type:** Story | **Points:** 5 (L) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-01, S4-01

#### Context (read before starting)
- `modules/07-utilization-dashboards/SCREENS.md` → Company Dashboard spec
- `modules/07-utilization-dashboards/mockups/company-dashboard.html` → Visual mockup reference

#### Description
As a CEO/CTO, I want a visual company dashboard so that I can see the business at a glance.

#### Acceptance Criteria
- [ ] `/dashboard` route — grid of KPI widgets
- [ ] Billable Utilization % — large number with color (green ≥70%, amber 50-69%, red <50%)
- [ ] Bench Count — number card with expandable list of benched resources (name, designation, days on bench), click → resource profile
- [ ] Shadow Allocation — count of shadow assignments + total shadow allocation %
- [ ] Active Projects — number card with breakdown bar (FP / T&M / Onboarding), click type → filtered project list
- [ ] Upcoming Releases — list of next 30d releases (resource, project, end date, days remaining), click → project detail
- [ ] Loading skeleton for each widget independently
- [ ] Phase 2 financial widgets: placeholder cards with "Coming in Phase 2" label
- [ ] Auth: CEO/CTO only — redirect others to `/availability` or `/my-assignments`
- [ ] Each widget: "—" or "0" for empty state (no data)
- [ ] Responsive: widgets reflow on smaller screens

---

### S5-05: Resource Availability View UI
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-03, S4-01

#### Context (read before starting)
- `modules/07-utilization-dashboards/SCREENS.md` → Resource Availability View spec
- `modules/07-utilization-dashboards/mockups/availability.html` → Visual mockup reference

#### Description
As any user, I want a resource availability page so that I can find available team members.

#### Acceptance Criteria
- [ ] `/availability` route — 4 sections (tabs or scroll sections)
- [ ] Bench section: resource cards with name, designation, expertise, days on bench, tags
- [ ] Partial section: resource cards with name, total allocation %, spare capacity %, project names
- [ ] Releasing Soon section: list with name, project, allocation %, end date, days remaining
- [ ] Fully Allocated section: list with name, total allocation %, project names
- [ ] 30/60/90 day toggle for Releasing Soon
- [ ] Search by resource name (filters across all sections)
- [ ] Click resource → `/resources/:id` (if role has access)
- [ ] Click project → `/projects/:id` (if role has access)
- [ ] Empty section: "No resources currently on bench." (per section)
- [ ] No financial data shown anywhere

---

### S5-06: Dashboard integration tests
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-01 through S5-03

#### Context (read before starting)
- `shared/BUSINESS-RULES.md` → §7.1 utilization formulas
- `CLAUDE.md` → Testing Expectations

#### Description
As a developer, I want dashboard tests so that aggregation queries and access control are verified.

#### Acceptance Criteria
- [ ] Company dashboard: correct utilization % with known data (3 resources, 5 assignments → expected %)
- [ ] Bench count correct after releasing an assignment
- [ ] Upcoming releases returns only assignments ending within window
- [ ] DM dashboard scoped correctly (doesn't include other DM's projects)
- [ ] Availability sections correctly categorized
- [ ] CEO/CTO access only on company dashboard (403 for PM)
- [ ] Availability endpoint accessible to Engineer
- [ ] Financial fields return null

---

## EP-7: Worklog (15 SP)

### S5-07: Worklog database schema and migration
**Type:** Story | **Points:** 1 (XS) | **Priority:** P0 — Blocker
**Labels:** `database`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S3-06, S2-01

#### Context (read before starting)
- `modules/11-worklog/SCHEMA.md` — exact field definitions
- `shared/ENTITIES.md` → Worklog entity

#### Description
As a developer, I want the worklogs table so that engineers can log hours.

#### Acceptance Criteria
- [ ] Alembic migration creates `worklogs` table: id (UUID PK), resource_id (FK→resources NOT NULL), project_id (FK→projects NOT NULL), log_date (DATE NOT NULL), hours (DECIMAL(4,1) NOT NULL), note (TEXT NULLABLE), created_at (TIMESTAMP)
- [ ] Indexes on: resource_id, project_id, log_date
- [ ] Unique constraint: (resource_id, project_id, log_date)
- [ ] SQLAlchemy model in `app/modules/worklogs/models.py`
- [ ] Migration reversible

---

### S5-08: Worklog CRUD API with validations
**Type:** Story | **Points:** 3 (M) | **Priority:** P0 — Blocker
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-07, S1-03

#### Context (read before starting)
- `modules/11-worklog/API.md` — all endpoints
- `modules/11-worklog/SCHEMA.md` → field definitions

#### Description
As an engineer, I want to log hours on my assigned projects.

#### Acceptance Criteria
- [ ] `GET /api/v1/worklogs/my` — own entries, paginated, with ?project_id, ?start_date, ?end_date filters
- [ ] `POST /api/v1/worklogs` — create entry with resource_id from current user
- [ ] `PUT /api/v1/worklogs/:id` — update hours and note only (cannot change project_id or log_date)
- [ ] `DELETE /api/v1/worklogs/:id` — owner only
- [ ] **5 validations:**
  1. Project must have worklog_enabled=true
  2. Resource must have (or have had) ACTIVE assignment on this project covering log_date
  3. log_date cannot be in the future
  4. hours must be 0.5–24.0 in 0.5 increments
  5. One entry per resource+project+day (409 on duplicate)
- [ ] No audit logging required (informational, no financial impact)
- [ ] Pydantic schemas in `app/modules/worklogs/schemas.py`

---

### S5-09: Worklog manager view API
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-08

#### Context (read before starting)
- `modules/11-worklog/API.md` → GET /projects/:projectId/worklogs, GET /resources/:resourceId/worklogs

#### Description
As a PM/DM, I want to view worklog entries for my projects and resources.

#### Acceptance Criteria
- [ ] `GET /api/v1/projects/:projectId/worklogs` — paginated, with ?resource_id, ?start_date, ?end_date
- [ ] `GET /api/v1/resources/:resourceId/worklogs` — paginated, with ?project_id, ?start_date, ?end_date
- [ ] Project worklogs: CEO, CTO (ALL), DM/PM (OWN_PORTFOLIO)
- [ ] Resource worklogs: CEO, CTO, DM/PM (own portfolio), resource owner (SELF_ONLY)
- [ ] Each entry includes resource name and project name

---

### S5-10: Worklog Entry UI (My Assignments)
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-08, S4-01

#### Context (read before starting)
- `modules/11-worklog/SCREENS.md` → Worklog Entry spec
- `modules/11-worklog/mockups/worklog-entry.html` → Visual mockup reference
- `modules/07-utilization-dashboards/SCREENS.md` → My Assignments spec
- `modules/07-utilization-dashboards/mockups/my-assignments.html` → Visual mockup reference

#### Description
As an engineer, I want a page where I can see my assignments and log hours.

#### Acceptance Criteria
- [ ] `/my-assignments` route — active assignment cards + worklog form
- [ ] Assignment cards: project name, client, allocation %, start date, end date
- [ ] Worklog section: project selector (pre-populated from worklog-enabled assignments)
- [ ] Date picker (defaults to today, blocks future dates)
- [ ] Hours input (0.5–24.0 in 0.5 steps — spinner or dropdown)
- [ ] Note textarea (optional)
- [ ] "Log Hours" button → POST /api/v1/worklogs
- [ ] Recent entries table (last 30 days): date, project, hours, note, edit/delete buttons
- [ ] Edit → modal with hours + note fields
- [ ] Delete → confirmation dialog
- [ ] Validation messages match spec: "Worklog is not enabled for this project", "Hours must be between 0.5 and 24", etc.
- [ ] If no worklog-enabled projects: "No projects with worklog enabled."
- [ ] If no assignments: "You have no active project assignments."

---

### S5-11: Worklog Tab in Project Detail
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `frontend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-09, S4-03

#### Context (read before starting)
- `modules/11-worklog/SCREENS.md` → Worklog Tab spec
- `modules/11-worklog/mockups/worklog-tab.html` → Visual mockup reference

#### Description
As a PM/DM, I want to see worklog entries in the project detail so that I can track hours logged.

#### Acceptance Criteria
- [ ] Worklogs tab in project detail — shown only when worklog_enabled=true
- [ ] Date range filter (start/end date pickers)
- [ ] Resource filter dropdown (resources assigned to this project)
- [ ] Table: Date, Resource Name, Hours, Note (truncated with expand)
- [ ] Pagination
- [ ] Empty state: "No worklog entries for this period."
- [ ] Tab hidden for projects with worklog_enabled=false

---

### S5-12: Worklog integration tests
**Type:** Story | **Points:** 2 (S) | **Priority:** P1 — Critical
**Labels:** `testing`, `backend`, `phase-1`, `must-have`, `agentic`
**Depends On:** S5-07 through S5-09

#### Context (read before starting)
- `modules/11-worklog/API.md` → all endpoints
- `CLAUDE.md` → Testing Expectations

#### Description
As a developer, I want worklog tests so that all 5 validations and access control are verified.

#### Acceptance Criteria
- [ ] Create happy path: valid entry succeeds
- [ ] Validation: worklog_enabled=false → 400
- [ ] Validation: no active assignment → 400
- [ ] Validation: future date → 422
- [ ] Validation: hours < 0.5 or > 24 → 422
- [ ] Validation: duplicate (resource, project, date) → 409
- [ ] Update: can change hours/note, cannot change project/date
- [ ] Delete: owner only (403 for other users)
- [ ] Manager view: DM sees only own portfolio project worklogs
- [ ] Resource worklogs: Engineer sees only own

---

## EP-9: Integration Testing & Polish (4 SP)

### S5-13: End-to-end smoke tests
**Type:** Story | **Points:** 3 (M) | **Priority:** P1 — Critical
**Labels:** `testing`, `phase-1`, `must-have`, `agentic`
**Depends On:** All previous sprints

#### Context (read before starting)
- `CLAUDE.md` → Testing Expectations
- All module REQUIREMENTS.md files → acceptance criteria

#### Description
As a developer, I want E2E smoke tests covering the critical path so that Phase 1 is verified end-to-end.

#### Acceptance Criteria
- [ ] **Golden path test:** Login as CEO → create client → create project → assign resource → verify dashboard updates → log worklog → verify worklog in project detail
- [ ] **RBAC smoke test:** Login as each of 7 roles → verify correct sidebar nav items visible → verify correct 403s on unauthorized endpoints (sample 3 endpoints per role)
- [ ] **Data cascade test:** Deactivate resource → verify assignments released → verify bench count increases
- [ ] **Status lifecycle test:** Create project → complete project → verify assignments released → verify project cannot transition further
- [ ] **Auto-release simulation:** Create assignment with end_date=today → trigger auto-release job → verify status=AUTO_RELEASED + alerts created
- [ ] All tests run in CI with test database
- [ ] Tests use the test fixtures from S1-09 conftest.py

---

### S5-14: Phase 1 hardening and cleanup
**Type:** Story | **Points:** 1 (XS) | **Priority:** P2 — Major
**Labels:** `devops`, `phase-1`, `nice-to-have`, `agentic`
**Depends On:** All previous sprints

#### Context (read before starting)
- All code written in Sprints 0-5

#### Description
As a developer, I want to clean up tech debt from Phase 1 before moving to Phase 2.

#### Acceptance Criteria
- [ ] All TODO comments resolved or converted to tracked issues
- [ ] No unused imports or dead code
- [ ] All API endpoints have OpenAPI/Swagger documentation (FastAPI auto-docs verify)
- [ ] `.env.example` updated with all env vars used across all modules
- [ ] Seed script updated with any new seed data added during sprints
- [ ] Docker Compose still boots cleanly with fresh DB
- [ ] CI pipeline green on all checks
- [ ] README updated with: current module status, how to run locally, how to run tests

---

## Sprint 5 Summary

| Story | Title | SP | Epic | Labels | Priority |
|-------|-------|---|------|--------|----------|
| S5-01 | Company dashboard API | 3 | EP-6 | backend | P1 |
| S5-02 | DM portfolio dashboard API | 2 | EP-6 | backend | P1 |
| S5-03 | Resource availability API | 3 | EP-6 | backend | P1 |
| S5-04 | Company Dashboard UI | 5 | EP-6 | frontend | P1 |
| S5-05 | Resource Availability UI | 3 | EP-6 | frontend | P1 |
| S5-06 | Dashboard integration tests | 2 | EP-6 | testing | P1 |
| S5-07 | Worklog schema + migration | 1 | EP-7 | database, backend | P0 |
| S5-08 | Worklog CRUD + 5 validations | 3 | EP-7 | backend | P0 |
| S5-09 | Worklog manager view API | 2 | EP-7 | backend | P1 |
| S5-10 | Worklog Entry UI | 3 | EP-7 | frontend | P1 |
| S5-11 | Worklog Tab in Project Detail | 2 | EP-7 | frontend | P1 |
| S5-12 | Worklog integration tests | 2 | EP-7 | testing | P1 |
| S5-13 | E2E smoke tests | 3 | EP-9 | testing | P1 |
| S5-14 | Phase 1 hardening | 1 | EP-9 | devops | P2 |
| **Total** | | **35** | | | |
